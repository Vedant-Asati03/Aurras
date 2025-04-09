"""
Core MPV player implementation.

This module provides the main MPV player implementation that integrates
all the functionality from other modules into a cohesive player experience.
"""

import time
import locale
import logging
import gc
from concurrent.futures import ThreadPoolExecutor
from collections import deque
from typing import Dict, Any, List, Optional, Tuple

from rich.live import Live
from rich.console import Group

from ...core.settings import KeyboardShortcuts, Settings
from ...utils.console_manager import get_console
from ...utils.exceptions import DisplayError
from ..python_mpv import MPV, ShutdownError
from ..lyrics_handler import LyricsHandler
from ..history import RecentlyPlayedManager
from ..cache import LRUCache
from ..memory import memory_stats_decorator, optimize_memory_usage

from .state import (
    PlaybackState,
    LyricsStatus,
    FeedbackType,
    HistoryCategory,
    Metadata,
    PlayerState,
    UserFeedback,
    HistoryData,
    LyricsState,
)
from .events import create_property_observers
from .keyboard import setup_key_bindings
from .ui import (
    create_display_content,
    create_player_panel,
    get_controls_text,
    format_song_info,
    get_status_text,
)
from .lyrics_integration import prefetch_lyrics, get_lyrics_display

logger = logging.getLogger(__name__)
PLAYERSETTINGS = Settings()
KEYBOARDSHORTCUTS = KeyboardShortcuts()


class MPVPlayer(MPV):
    """
    Enhanced MPV player with rich UI and extended functionality.

    This class provides a carefully designed player interface with:
    - Rich terminal UI with progress bar and metadata display
    - Lyrics integration using the unified database
    - History integration for continuous playback
    - Enhanced keyboard controls
    - Optimized performance

    Attributes:
        console: Rich console for UI rendering
        lyrics_handler: Handler for lyrics operations
        volume: Current volume level (0-130)
    """

    def __init__(
        self,
        ytdl: bool = True,
        ytdl_format: str = "bestaudio",
        volume: int = PLAYERSETTINGS.default_volume,
        loglevel: str = "warn",
    ) -> None:
        """
        Initialize the enhanced MPV player with optimized settings.

        Args:
            ytdl: Whether to enable YouTube-DL integration
            ytdl_format: Format string for YouTube-DL
            volume: Initial volume level (0-130)
            loglevel: Logging level for MPV messages
        """
        # Set locale for proper number formatting
        locale.setlocale(locale.LC_NUMERIC, "C")

        # Initialize base MPV player
        super().__init__(
            ytdl=ytdl,
            ytdl_format=ytdl_format,
            input_default_bindings=True,
            input_vo_keyboard=True,
            video=False,
            terminal=True,
            input_terminal=True,
        )

        # Set up core components
        self.console = get_console()
        self.lyrics_handler = LyricsHandler()
        # Use a smaller thread pool and make it context-managed
        self._thread_pool = ThreadPoolExecutor(max_workers=2).__enter__()
        self.history_manager = RecentlyPlayedManager()

        # Initialize state using dataclasses
        self._init_state_properties(volume)
        self._configure_mpv(loglevel)

        # Setup property observers and key bindings
        self._observers = create_property_observers(self)
        setup_key_bindings(self)

        # Track active futures for proper cleanup
        self._active_futures = set()

        # Set up time position observer
        @self.property_observer("time-pos")
        def _track_time_pos(_name: str, value: Optional[float]) -> None:
            # This is safe because it's a primitive type (float)
            # and doesn't create circular references
            if hasattr(self, "_state"):
                self._state.elapsed_time = value if value is not None else 0

    def _init_state_properties(self, volume: int) -> None:
        """Initialize all state properties with default values using dataclasses."""
        # Initialize dataclasses for state management
        self._state = PlayerState(
            show_lyrics=True if PLAYERSETTINGS.display_lyrics == "yes" else False
        )
        self._metadata = Metadata()
        self._history = HistoryData()
        self._lyrics = LyricsState(
            status=LyricsStatus.DISABLED
            if PLAYERSETTINGS.display_lyrics != "yes"
            else LyricsStatus.LOADING
        )
        self._user_feedback: Optional[UserFeedback] = None

        # Use a fixed-size list for caching to prevent memory growth
        self._lyrics_cache = LRUCache(max_size=5)  # Cache last 5 lyrics
        self._metadata_cache = LRUCache(max_size=10)  # Cache last 10 metadata objects

        # Playlist state - use a deque for better memory performance with large lists
        self._current_song_names = deque(maxlen=1000)  # Limit to 1000 songs max

        # Set initial volume
        self.volume = volume

        # Memory tracking
        self._memory_stats = {
            "peak_lyrics_size": 0,
            "peak_metadata_size": 0,
            "last_gc_time": time.time(),
        }

    def _configure_mpv(self, loglevel: str) -> None:
        """Configure MPV settings for optimal playback."""
        self._set_property("msg-level", f"all={loglevel}")
        self._set_property("audio-buffer", 2.0)  # Increase buffer size
        self._set_property("cache", "yes")  # Enable cache

    # --- Event Handlers ---

    def _on_pause_change(self, _name: str, value: Optional[bool]) -> None:
        """
        Handle pause property changes.

        Args:
            _name: Property name
            value: New pause state
        """
        if value is None:
            return

        try:
            status = "Paused" if value else "Playing"
            logger.debug(f"Playback state changed to {status}")

            # Update playback state enum
            self._state.playback_state = (
                PlaybackState.PAUSED if value else PlaybackState.PLAYING
            )
            self._state.current_refresh_rate = 1.0 if value else 0.25

            self._show_user_feedback(
                "Pause" if value else "Play",
                f"Playback {status.lower()}",
                FeedbackType.PLAYBACK,
            )
        except Exception as e:
            logger.error(f"Error in pause change handler: {e}")

    def _on_duration_change(self, _name: str, value: Optional[float]) -> None:
        """
        Handle duration property changes.

        Args:
            _name: Property name
            value: New duration in seconds
        """
        if value and value > 0:
            self._metadata.duration = value
            logger.debug(f"Duration updated to {value:.2f} seconds")

            # When duration changes, we probably have metadata
            self._check_metadata_complete()

    def _on_metadata_change(self, _name: str, value: Optional[Dict[str, Any]]) -> None:
        """
        Handle metadata changes.

        Args:
            _name: Property name
            value: New metadata dictionary
        """
        if not value:
            return

        changed = False

        # Update simple metadata fields
        for field in ["title", "artist", "album"]:
            if field in value and value[field] != getattr(self._metadata, field):
                setattr(self._metadata, field, value[field])
                changed = True

        # Special handling for streaming metadata
        if "icy-title" in value and "title" not in value:
            icy_title = value["icy-title"]
            if " - " in icy_title:
                artist, title = icy_title.split(" - ", 1)
                self._metadata.artist = artist
                self._metadata.title = title
                changed = True
            else:
                self._metadata.title = icy_title
                changed = True

        if changed:
            logger.debug(f"Updated metadata: {self._metadata}")
            self._check_metadata_complete()

    def _on_playlist_pos_change(self, _name: str, value: Optional[int]) -> None:
        """
        Handle playlist position changes.

        Args:
            _name: Property name
            value: New playlist position
        """
        if value is None or not (0 <= value < len(self._current_song_names)):
            return

        old_pos = self._state.current_playlist_pos
        self._state.current_playlist_pos = value
        logger.debug(f"Playlist position changed from {old_pos} to {value}")

        # Reset metadata and lyrics for new song
        self._state.metadata_ready = False
        self._metadata.title = "Unknown"
        self._metadata.artist = "Unknown"
        self._metadata.album = "Unknown"

        # Thoroughly reset lyrics state
        self._lyrics.cached_lyrics = None
        self._lyrics.no_lyrics_message = None
        self._lyrics.status = LyricsStatus.LOADING

        # Also clear from lyrics cache to ensure fresh fetch
        if hasattr(self, "_lyrics_cache"):
            song_name = self._current_song_names[value]
            # Use the remove method of LRUCache which handles the lookup properly
            self._lyrics_cache.remove(song_name) if hasattr(
                self._lyrics_cache, "remove"
            ) else None

        self._history.loaded = False  # Reset history data

        # Cancel any pending lyrics fetch
        if self._lyrics.future and not self._lyrics.future.done():
            self._lyrics.future.cancel()
            self._lyrics.future = None  # Ensure future is fully reset

        # Show user feedback for track change
        song_name = self._current_song_names[value]
        self._show_user_feedback(
            "Track Change", f"Playing: {song_name}", FeedbackType.NAVIGATION
        )

        # Log when transitioning between history and searched songs
        if value == self._state.queue_start_index and self._state.queue_start_index > 0:
            logger.info("Now playing first searched song (after history)")
        elif value == 0 and self._state.queue_start_index > 0:
            logger.info("Now playing from history songs")

    # --- Main Player API ---

    @memory_stats_decorator(interval_seconds=30)
    def player(
        self,
        queue: List[str],
        song_names: List[str],
        show_lyrics: bool = True,
        start_index: int = 0,
    ) -> int:
        """
        Main entry point for playing media with enhanced UI.

        Args:
            queue: List of URLs to play
            song_names: List of song names corresponding to the URLs
            show_lyrics: Whether to show lyrics
            start_index: Index in the queue to start from (for history integration)

        Returns:
            Result code (0 for success)
        """
        # Initialize playback state
        self._state.stop_requested = False
        self._state.playback_state = PlaybackState.PLAYING
        self._state.show_lyrics = show_lyrics
        if show_lyrics:
            self._lyrics.status = LyricsStatus.LOADING
        else:
            self._lyrics.status = LyricsStatus.DISABLED

        self._current_song_names = song_names.copy()
        self._state.queue_start_index = start_index

        try:
            # Log playback information
            logger.info(
                f"Playing queue with {len(queue)} songs, starting at {start_index}"
            )

            self._initialize_player(queue, start_index)

            # Start display
            first_song = (
                song_names[start_index]
                if 0 <= start_index < len(song_names)
                else "Unknown"
            )
            self._start_display(first_song)

            # Wait for playback to complete - use a safe check here to prevent ShutdownError
            try:
                if not self._state.stop_requested:
                    # Safely check playlist_count with error handling
                    playlist_count = self._safe_get_property("playlist_count", 0)
                    if playlist_count:
                        self.wait_for_playback()

                    # Track memory stats periodically during display loop
                    if hasattr(self, "_log_memory_stats") and self._run_display_loop:
                        self._log_memory_stats()
            except ShutdownError:
                logger.debug(
                    "MPV core shutdown detected during playback, exiting cleanly"
                )
                # Already handled by quit/terminate, just continue to cleanup
                pass

            return 0

        except KeyboardInterrupt:
            self.console.print("\n[yellow]Playback interrupted by user[/]")
            return 1
        except ShutdownError:
            # This is actually normal when using quit, so don't show as error
            logger.debug("MPV core shutdown detected, exiting cleanly")
            return 0
        except Exception as e:
            logger.error(f"Error during playback: {e}", exc_info=True)
            self.console.print(f"[bold red]Playback error: {str(e)}[/]")
            return 2
        finally:
            # Clean up resources
            self._stop_display()
            if self._thread_pool:
                self._thread_pool.shutdown(wait=False)
            # Final memory cleanup
            self.cleanup_resources()
            # Force garbage collection before exit
            gc.collect()

    def _initialize_player(self, queue: List[str], start_index: int = 0) -> None:
        """
        Initialize player with queue and start playback.

        Args:
            queue: List of URLs to play
            start_index: Index to start playback from
        """
        for i, url in enumerate(queue):
            if url and url.strip():  # Ensure URL is not empty
                logger.info(f"Using URL for playback: {url}")
                self.playlist_append(url)
            else:
                # If both are empty, log error
                logger.error(f"No valid URL or file path for song at position {i}")
                # Add a placeholder to maintain playlist ordering
                self.playlist_append("null://")

        # Set the starting position
        logger.info(f"Starting playback at index {start_index}")
        self._state.current_playlist_pos = start_index
        if self.playlist_count > 0:
            self.playlist_play_index(start_index)
        else:
            logger.error("No playable items in playlist")

    def _start_display(self, song_name: str) -> None:
        """Start the live display UI."""
        # Run the display directly
        self._run_display(song_name)

    def _stop_display(self) -> None:
        """Stop the display cleanly."""
        self._state.stop_requested = True

    def _run_display(self, song_name: str) -> None:
        """
        Run the live display UI showing playback information and controls.

        Args:
            song_name: The initial song name to display
        """
        try:
            # Define control key information
            controls_text = get_controls_text()

            # Initialize display state
            last_song = None
            metadata_ready = False
            refresh_count = 0

            # Create the live display using our console from the manager
            with Live(
                refresh_per_second=4, console=self.console, transient=True
            ) as live:
                # Use playback_state enum instead of is_playing attribute
                while (
                    not self._state.stop_requested
                    and self._state.playback_state != PlaybackState.STOPPED
                ):
                    try:
                        # Current position and song info
                        current_song = self._get_current_song_name()
                        elapsed = self._state.elapsed_time or 0
                        duration = self._metadata.duration
                        artist = self._metadata.artist
                        album = self._metadata.album

                        # Check if song changed
                        song_changed = current_song != last_song
                        if song_changed:
                            last_song = current_song
                            metadata_ready = False
                            refresh_count = 0
                        else:
                            refresh_count += 1

                        # Check metadata readiness
                        if not metadata_ready and refresh_count > 2:
                            metadata_ready = self._state.metadata_ready

                        # Process lyrics if enabled
                        lyrics_section = ""
                        if self._state.show_lyrics:
                            lyrics_section = get_lyrics_display(
                                current_song,
                                artist,
                                album,
                                elapsed,
                                duration,
                                metadata_ready,
                                self._lyrics,
                                self.lyrics_handler,
                            )

                        # Load history data if needed
                        if not self._history.loaded:
                            self._load_history_data(current_song)

                        # Get history text
                        history_text = self._get_history_text(current_song)

                        # Create the content for display
                        content = create_display_content(
                            current_song,
                            artist,
                            album,
                            elapsed,
                            duration,
                            self._state.playback_state,
                            self._safe_get_property("volume", 0),
                            self._state.current_theme,
                            self._state.current_playlist_pos,
                            len(self._current_song_names),
                            self._user_feedback,
                            history_text,
                            lyrics_section,
                        )

                        # Create panel with user feedback if available
                        panel = create_player_panel(content, controls_text)

                        # Update the display
                        live.update(panel)

                        # Apply appropriate refresh rate
                        time.sleep(self._state.current_refresh_rate)

                    except ShutdownError:
                        # Handle mpv shutdown gracefully
                        self._state.stop_requested = True
                        break
                    except Exception as e:
                        # Log errors but continue
                        logger.error(f"Display update error: {e}")
                        time.sleep(1.0)

        except Exception as e:
            logger.error(f"Display thread error: {e}")
            raise DisplayError(f"Display error: {e}")

    def _check_metadata_complete(self) -> None:
        """Check if we have complete metadata and start lyrics lookup if needed."""
        title = self._metadata.title
        duration = self._metadata.duration
        artist = self._metadata.artist

        # Consider metadata ready if we have at least title and duration
        metadata_complete = title != "Unknown" and artist != "Unknown" and duration > 0

        if metadata_complete and not self._state.metadata_ready:
            self._state.metadata_ready = True
            song = title

            album = self._metadata.album

            if self._state.show_lyrics and self.lyrics_handler.has_lyrics_support():
                logger.debug(f"Starting async lyrics lookup for '{song}'")
                self._prefetch_lyrics(song, artist, album, int(duration))

    @optimize_memory_usage()
    def _prefetch_lyrics(
        self, song: str, artist: str, album: str, duration: int
    ) -> None:
        """
        Prefetch lyrics asynchronously with optimized memory usage.

        Args:
            song: Song name
            artist: Artist name
            album: Album name
            duration: Song duration in seconds
        """
        # Skip if we already have cached lyrics for this song
        if self._lyrics.cached_lyrics:
            self._lyrics.status = LyricsStatus.AVAILABLE
            return

        # Cancel any existing future to avoid memory leaks
        if self._lyrics.future and not self._lyrics.future.done():
            self._lyrics.future.cancel()

        # Use the prefetch_lyrics function from lyrics_integration module
        self._lyrics.future = prefetch_lyrics(
            song,
            artist,
            album,
            duration,
            self.lyrics_handler,
            self._lyrics_cache,
            self._thread_pool,
            self._active_futures,
        )

    # --- Utility Methods ---

    def _get_current_song_name(self) -> str:
        """Get the name of the currently playing song."""
        if 0 <= self._state.current_playlist_pos < len(self._current_song_names):
            return self._current_song_names[self._state.current_playlist_pos]
        return "Unknown"

    def _get_song_source(self) -> str:
        """Get the source indicator for the current song (history or searched)."""
        source_text = ""

        # Check if song is from history
        if (
            self._state.current_playlist_pos < self._state.queue_start_index
            and self._state.queue_start_index > 0
        ):
            source_text = " [dim](From History)[/dim]"

        return source_text

    def _load_history_data(self, song_name: str) -> None:
        """
        Load play history data for the current song.

        Args:
            song_name: Name of the current song
        """
        try:
            # Get all recent songs
            recent_songs = self.history_manager.get_recent_songs(1000)

            # Find the current song in history
            matching_songs = [s for s in recent_songs if s["song_name"] == song_name]

            if matching_songs:
                # If found in history, get play count and last played time
                song_data = matching_songs[0]
                self._history.play_count = song_data.get("play_count", 1)
                self._history.last_played = song_data.get("played_at", 0)

                # Set the history category based on play count
                if self._history.play_count > 10:
                    self._history.category = HistoryCategory.FAVORITE
                elif self._history.play_count > 5:
                    self._history.category = HistoryCategory.REGULAR
                elif self._history.play_count > 1:
                    self._history.category = HistoryCategory.OCCASIONAL
                else:
                    self._history.category = HistoryCategory.NEW
            else:
                # If not found in history, reset values
                self._history.play_count = 0
                self._history.last_played = None
                self._history.category = HistoryCategory.NEW

            self._history.loaded = True
            logger.debug(
                f"Loaded history for '{song_name}': count={self._history.play_count}, category={self._history.category.name}"
            )

        except Exception as e:
            logger.error(f"Error loading history data: {e}")
            self._history.play_count = 0
            self._history.last_played = None
            self._history.category = HistoryCategory.NEW
            self._history.loaded = (
                True  # Still mark as loaded to prevent repeated attempts
            )

    def _get_history_text(self, song_name: str) -> Optional[str]:
        """
        Get formatted history information text for the current song.

        Args:
            song_name: Name of the current song

        Returns:
            Formatted history text or None if not available
        """
        if not self._history.loaded or self._history.play_count <= 1:
            return None

        # Format the play count with appropriate styling
        if self._history.play_count > 10:
            count_text = f"[bold gold1]You've played this {self._history.play_count} times![/bold gold1]"
        elif self._history.play_count > 5:
            count_text = (
                f"[yellow]You've played this {self._history.play_count} times[/yellow]"
            )
        elif self._history.play_count > 1:
            count_text = (
                f"[dim]You've played this {self._history.play_count} times[/dim]"
            )
        else:
            return None

        # Format the last played info if available
        last_played_text = ""
        if self._history.last_played:
            current_time = int(time.time())
            time_diff = current_time - self._history.last_played

            if time_diff < 3600:  # Less than an hour
                minutes = time_diff // 60
                last_played_text = f"[dim]Last played: {minutes} minute{'s' if minutes != 1 else ''} ago[/dim]"
            elif time_diff < 86400:  # Less than a day
                hours = time_diff // 3600
                last_played_text = f"[dim]Last played: {hours} hour{'s' if hours != 1 else ''} ago[/dim]"
            else:
                days = time_diff // 86400
                last_played_text = (
                    f"[dim]Last played: {days} day{'s' if days != 1 else ''} ago[/dim]"
                )

        # Combine the information
        if last_played_text:
            return f"\n{count_text} · {last_played_text}"
        else:
            return f"\n{count_text}"

    def _show_user_feedback(
        self,
        action: str,
        description: str,
        feedback_type: FeedbackType,
        timeout: float = 1.5,
    ) -> None:
        """
        Show user feedback for an action in the UI.

        Args:
            action: Short name of the action
            description: Longer description of what happened
            feedback_type: Feedback type category
            timeout: How long to show the feedback (seconds)
        """
        should_show_feedback = (
            True if PLAYERSETTINGS.user_feedback_visible == "yes" else False
        )

        if should_show_feedback:
            self._user_feedback = UserFeedback(
                action=action,
                description=description,
                feedback_type=feedback_type,
                timestamp=time.time(),
                timeout=timeout,
            )

    def _is_paused(self) -> bool:
        """Safely check if the player is in paused state."""
        try:
            # Use safe_get_property instead of direct property access
            paused = self._safe_get_property("pause", False)
            return bool(paused)
        except Exception as e:
            # If we can't access the pause property, use our state
            logger.debug(f"Could not access pause property: {e}")
            return self._state.playback_state == PlaybackState.PAUSED

    # Add a helper method for safe property access
    def _safe_get_property(self, name: str, default=None):
        """Safely get a property, returning default if any error occurs."""
        try:
            if hasattr(self, "_core_shutdown") and self._core_shutdown:
                return default

            if self._state.stop_requested:
                return default

            # Use direct property access but catch any exceptions
            try:
                value = getattr(self, name)
                return value
            except (ShutdownError, AttributeError) as e:
                logger.debug(f"Property access failed for {name}: {e}")
                return default
        except Exception as e:
            logger.debug(f"Safe property access failed: {e}")
            return default

    def _execute_playlist_jump(self, jump_amount: int) -> None:
        """
        Jump forward or backward in the playlist by the specified number of tracks.

        Args:
            jump_amount: Number of tracks to jump (positive for forward, negative for backward)
        """
        try:
            # Calculate the new position
            current_pos = self._state.current_playlist_pos
            new_pos = current_pos + jump_amount

            # Ensure the new position is within valid bounds
            playlist_length = len(self._current_song_names)
            if playlist_length <= 0:
                return

            # Handle wraparound if enabled in settings
            enable_wraparound = (
                getattr(PLAYERSETTINGS, "playlist_wraparound", "yes") == "yes"
            )
            if enable_wraparound:
                # Wrap around if we go beyond the ends of the playlist
                new_pos = new_pos % playlist_length
            else:
                # Clamp to valid range without wraparound
                new_pos = max(0, min(new_pos, playlist_length - 1))

            # Only jump if the position has changed
            if new_pos != current_pos:
                logger.debug(f"Jumping from position {current_pos} to {new_pos}")
                # Update our internal state
                self._state.current_playlist_pos = new_pos
                # Tell MPV to play the track at the new position
                self.playlist_play_index(new_pos)
        except Exception as e:
            logger.error(f"Error executing playlist jump: {e}")
            # Show user feedback about the error
            self._show_user_feedback(
                "Jump Error", f"Failed to jump: {str(e)}", FeedbackType.ERROR
            )

    # --- Public API ---

    def get_playback_info(self) -> Dict[str, Any]:
        """
        Get current playback information.

        Returns:
            Dictionary with playback state, position, duration, volume and metadata
        """
        try:
            if self._state.stop_requested:
                raise ShutdownError("Player is shutting down")

            return {
                "is_playing": self._state.playback_state == PlaybackState.PLAYING,
                "position": self._safe_get_property("time_pos", 0),
                "duration": self._safe_get_property("duration", 0),
                "volume": self._safe_get_property("volume", 0),
                "metadata": {
                    "title": self._metadata.title,
                    "artist": self._metadata.artist,
                    "album": self._metadata.album,
                    "duration": self._metadata.duration,
                },
                "playlist_position": self._state.current_playlist_pos,
                "playlist_count": len(self._current_song_names),
                "lyrics_status": self._lyrics.status.name,
            }
        except ShutdownError:
            return {
                "is_playing": False,
                "position": 0,
                "duration": 0,
                "volume": 0,
                "metadata": {},
                "playlist_position": 0,
                "playlist_count": 0,
                "lyrics_status": LyricsStatus.DISABLED.name,
            }
        except Exception as e:
            logger.error(f"Error getting playback info: {e}")
            return {
                "is_playing": False,
                "position": 0,
                "duration": 0,
                "volume": 0,
                "metadata": {},
                "playlist_position": 0,
                "playlist_count": 0,
                "lyrics_status": LyricsStatus.DISABLED.name,
                "error": str(e),
            }

    def set_volume(self, volume: int) -> None:
        """
        Set the player volume.

        Args:
            volume: Volume level (0-130)
        """
        self.volume = max(0, min(PLAYERSETTINGS.maximum_volume, volume))
        logger.debug(f"Volume set to {self.volume}")

    # Ensure player shutdown is handled gracefully
    def terminate(self):
        """Properly terminate the player, shutting down MPV gracefully."""
        try:
            # Mark as stopping
            self._state.stop_requested = True
            self._state.playback_state = PlaybackState.STOPPED

            # Clean up thread pool
            if hasattr(self, "_thread_pool") and self._thread_pool:
                self._thread_pool.shutdown(wait=False)

            # Call parent terminate method
            super().terminate()
        except Exception as e:
            logger.error(f"Error terminating player: {e}")

    def quit(self, code=None):
        """Override quit to ensure clean shutdown."""
        try:
            # Mark as stopping first
            self._state.stop_requested = True
            self._state.playback_state = PlaybackState.STOPPED

            # Then call parent quit method
            super().quit(code)
        except Exception as e:
            logger.error(f"Error quitting player: {e}")

    def __del__(self):
        """Ensure proper cleanup of resources when object is garbage collected."""
        self.cleanup_resources()

    def cleanup_resources(self):
        """Properly clean up all resources to prevent memory leaks."""
        try:
            # Cancel any pending lyrics futures
            if (
                hasattr(self, "_lyrics")
                and self._lyrics.future
                and not self._lyrics.future.done()
            ):
                self._lyrics.future.cancel()

            # Clean up thread pool
            if hasattr(self, "_thread_pool") and self._thread_pool:
                try:
                    self._thread_pool.__exit__(None, None, None)
                except Exception as e:
                    logger.debug(f"Error shutting down thread pool: {e}")

            # Unregister all property observers
            try:
                if hasattr(self, "_observers"):
                    for observer in self._observers:
                        observer.unregister()
                    self._observers = []
            except Exception as e:
                logger.debug(f"Error unregistering observers: {e}")
        except Exception as e:
            logger.error(f"Error during resource cleanup: {e}")

        # Call parent cleanup if available
        try:
            super().__del__()
        except Exception:
            pass


class MP3Player:
    """Simplified facade for the MPV player component."""

    def __init__(self, volume: int = 100) -> None:
        self.player = MPVPlayer(volume=volume)

    def play(
        self,
        songs: List[str],
        urls: List[str],
        show_lyrics: bool = True,
        start_index: int = 0,
    ) -> int:
        """Play a list of songs with the given URLs."""
        return self.player.player(
            queue=urls,
            song_names=songs,
            show_lyrics=show_lyrics,
            start_index=start_index,
        )
