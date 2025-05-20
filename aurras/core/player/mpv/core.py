"""
Core MPV player implementation.

This module provides the main MPV player implementation that integrates
all the functionality from other modules into a cohesive player experience.
"""

import gc
import time
import locale
from collections import deque
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor

from aurras.core.player.mpv.ui import PlayerLayout
from aurras.core.player.mpv.keyboard import setup_key_bindings
from aurras.core.player.mpv.events import create_property_observers
from aurras.core.player.mpv.lyrics_integration import (
    prefetch_lyrics,
    get_lyrics_display,
)
from aurras.core.player.mpv.state import (
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
from aurras.core.player.cache import LRUCache
from aurras.core.player.python_mpv import MPV, ShutdownError
from aurras.core.player.history import RecentlyPlayedManager
from aurras.core.player.memory import memory_stats_decorator, optimize_memory_usage
from aurras.services.lyrics import LyricsManager
from aurras.utils.logger import get_logger
from aurras.core.settings import SETTINGS
from aurras.utils.console import console

logger = get_logger("aurras.core.player.mpv.core", log_to_console=False)


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
        lyrics_manager: Manager for lyrics operations
        volume: Current volume level (0-130)
    """

    def __init__(
        self,
        ytdl: bool = True,
        ytdl_format: str = "bestaudio",
        volume: int = SETTINGS.default_volume,
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

        super().__init__(
            ytdl=ytdl,
            ytdl_format=ytdl_format,
            input_default_bindings=True,
            input_vo_keyboard=True,
            video=False,
            terminal=True,
            input_terminal=True,
        )

        self.lyrics_manager = LyricsManager()  # Updated to LyricsManager
        # Use a smaller thread pool and make it context-managed
        self._thread_pool = ThreadPoolExecutor(max_workers=2).__enter__()
        self.history_manager = RecentlyPlayedManager()

        self._init_state_properties(volume)
        self._configure_mpv(loglevel)

        self._observers = create_property_observers(self)
        setup_key_bindings(self)

        self._active_futures = deque(maxlen=25)

        @self.property_observer("time-pos")
        def _track_time_pos(_name: str, value: Optional[float]) -> None:
            if hasattr(self, "_state"):
                self._state.elapsed_time = value if value is not None else 0

    def _init_state_properties(self, volume: int) -> None:
        """Initialize all state properties with default values using dataclasses."""
        self._state = PlayerState(
            show_lyrics=True
            if SETTINGS.appearance_settings.display_lyrics == "yes"
            else False
        )
        self._metadata = Metadata()
        self._history = HistoryData()
        self._lyrics = LyricsState(
            status=LyricsStatus.DISABLED
            if SETTINGS.appearance_settings.display_lyrics != "yes"
            else LyricsStatus.LOADING
        )
        self._user_feedback: Optional[UserFeedback] = None

        self._metadata_cache = LRUCache(max_size=10)

        self._current_song_names = deque(maxlen=200)

        self.volume = volume

        self._memory_stats = {
            "peak_lyrics_size": 0,
            "peak_metadata_size": 0,
            "last_gc_time": time.time(),
        }

    def _configure_mpv(self, loglevel: str) -> None:
        """Configure MPV settings for optimal playback."""
        self._set_property("msg-level", f"all={loglevel}")
        self._set_property("audio-buffer", 2.0)
        self._set_property("cache", "yes")

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

        for field in ["title", "artist", "album"]:
            if field in value and value[field] != getattr(self._metadata, field):
                setattr(self._metadata, field, value[field])
                changed = True

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

        self._state.metadata_ready = False
        self._metadata.title = "Unknown"
        self._metadata.artist = "Unknown"
        self._metadata.album = "Unknown"

        self._lyrics.cached_lyrics = None
        self._lyrics.no_lyrics_message = None
        self._lyrics.status = LyricsStatus.LOADING

        self._history.loaded = False

        if self._lyrics.future and not self._lyrics.future.done():
            self._lyrics.future.cancel()
            self._lyrics.future = None

        song_name = self._current_song_names[value]
        self._show_user_feedback(
            "Track Change", f"Playing: {song_name}", FeedbackType.NAVIGATION
        )

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
            logger.info(
                f"Playing queue with {len(queue)} songs, starting at {start_index}"
            )

            self._initialize_player(queue, start_index)

            first_song = (
                song_names[start_index]
                if 0 <= start_index < len(song_names)
                else "Unknown"
            )
            self._start_display(first_song)

            try:
                if not self._state.stop_requested:
                    playlist_count = self._safe_get_property("playlist_count", 0)
                    if playlist_count:
                        self.wait_for_playback()

                    if hasattr(self, "_log_memory_stats") and self._run_display_loop:
                        self._log_memory_stats()
            except ShutdownError:
                logger.debug(
                    "MPV core shutdown detected during playback, exiting cleanly"
                )
                pass

            return 0

        except KeyboardInterrupt:
            console.print_info("\nPlayback interrupted by user")
            return 1
        except ShutdownError:
            logger.debug("MPV core shutdown detected, exiting cleanly")
            return 0
        except Exception as e:
            logger.error(f"Error during playback: {e}", exc_info=True)
            console.print_error(f"Playback error: {str(e)}")
            return 2
        finally:
            self._stop_display()
            if self._thread_pool:
                self._thread_pool.shutdown(wait=False)
            self.cleanup_resources()
            gc.collect()

    def _initialize_player(self, queue: List[str], start_index: int = 0) -> None:
        """
        Initialize player with queue and start playback.

        Args:
            queue: List of URLs to play
            start_index: Index to start playback from
        """
        for i, url in enumerate(queue):
            if url and url.strip():
                logger.info(f"Using URL for playback: {url}")
                self.playlist_append(url)
            else:
                logger.error(f"No valid URL or file path for song at position {i}")
                self.playlist_append("null://")

        logger.info(f"Starting playback at index {start_index}")
        self._state.current_playlist_pos = start_index
        if self.playlist_count > 0:
            self.playlist_play_index(start_index)
        else:
            logger.error("No playable items in playlist")

    def _start_display(self, song_name: str) -> None:
        """Start the live display UI."""
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
            player_layout = PlayerLayout()

            last_song = None
            metadata_ready = False
            refresh_count = 0

            player_layout.start_live_ui(refresh_per_second=4.0)

            try:
                while (
                    not self._state.stop_requested
                    and self._state.playback_state != PlaybackState.STOPPED
                ):
                    try:
                        current_song = self._get_current_song_name()
                        elapsed = self._state.elapsed_time or 0
                        duration = self._metadata.duration
                        artist = self._metadata.artist
                        album = self._metadata.album

                        song_changed = current_song != last_song
                        if song_changed:
                            last_song = current_song
                            metadata_ready = False
                            refresh_count = 0
                        else:
                            refresh_count += 1

                        if not metadata_ready and refresh_count > 2:
                            metadata_ready = self._state.metadata_ready

                        # Check for lyrics and history without storing unused variables
                        if self._state.show_lyrics:
                            lyrics_section = get_lyrics_display(
                                elapsed,
                                duration,
                                metadata_ready,
                                self._lyrics,
                                self.lyrics_manager,  # Updated to LyricsManager
                            )

                        if not self._history.loaded:
                            self._load_history_data(current_song)

                        # Create player state dictionary for UI update
                        player_state = {
                            "song": current_song,
                            "artist": artist,
                            "album": album,
                            "elapsed": elapsed,
                            "duration": duration,
                            "playback_state": self._state.playback_state,
                            "volume": self._safe_get_property("volume", 0),
                            "theme": self._state.current_theme,
                            "playlist_position": self._state.current_playlist_pos,
                            "playlist_count": len(self._current_song_names),
                            "feedback": self._user_feedback,
                            "lyrics_lines": lyrics_section
                            if self._lyrics.status == LyricsStatus.AVAILABLE
                            else [],
                            # Add song_names to player_state for the queue display
                            "song_names": self._current_song_names,
                        }

                        # Toggle lyrics display in layout if needed
                        if (
                            self._state.show_lyrics
                            and player_layout.show_lyrics != self._state.show_lyrics
                        ):
                            player_layout.toggle_lyrics()

                        # Update the UI with current player state
                        player_layout.update(player_state)

                        time.sleep(self._state.current_refresh_rate)

                    except ShutdownError:
                        self._state.stop_requested = True
                        break
                    except Exception as e:
                        logger.error(f"Display update error: {e}")
                        time.sleep(1.0)
            finally:
                player_layout.stop_live_ui()

        except Exception as e:
            logger.error(f"Display thread error: {e}")
            # Don't crash the playback just because the display had an error
            pass

    def _check_metadata_complete(self) -> None:
        """Check if we have complete metadata and start lyrics lookup if needed."""
        title = self._metadata.title
        duration = self._metadata.duration
        artist = self._metadata.artist

        metadata_complete = title != "Unknown" and artist != "Unknown" and duration > 0

        if metadata_complete and not self._state.metadata_ready:
            self._state.metadata_ready = True
            song = title

            album = self._metadata.album

            if (
                self._state.show_lyrics and self.lyrics_manager.has_lyrics_support()
            ):  # Updated to LyricsManager
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
        if self._lyrics.cached_lyrics:
            self._lyrics.status = LyricsStatus.AVAILABLE
            return

        if self._lyrics.future and not self._lyrics.future.done():
            self._lyrics.future.cancel()

        self._lyrics.future = prefetch_lyrics(
            song,
            artist,
            album,
            duration,
            self.lyrics_manager,  # Updated to LyricsManager
            self._thread_pool,
            self._active_futures,
        )

    # --- Utility Methods ---

    def _get_current_song_name(self) -> str:
        """
        Retrieve the name of the currently playing song from the playlist.

        Returns:
            The name of the current song or "Unknown" if no valid song is playing
        """
        if 0 <= self._state.current_playlist_pos < len(self._current_song_names):
            return self._current_song_names[self._state.current_playlist_pos]
        return "Unknown"

    def _load_history_data(self, song_name: str) -> None:
        """
        Load and categorize play history data for the current song.

        Retrieves play count and last played time from history manager,
        then categorizes the song as FAVORITE, REGULAR, OCCASIONAL, or NEW
        based on play frequency.

        Args:
            song_name: Name of the current song
        """
        try:
            recent_songs = self.history_manager.get_recent_songs(1000)

            matching_songs = [s for s in recent_songs if s["song_name"] == song_name]

            if matching_songs:
                song_data = matching_songs[0]
                self._history.play_count = song_data.get("play_count", 1)
                self._history.last_played = song_data.get("played_at", 0)

                if self._history.play_count > 10:
                    self._history.category = HistoryCategory.FAVORITE
                elif self._history.play_count > 5:
                    self._history.category = HistoryCategory.REGULAR
                elif self._history.play_count > 1:
                    self._history.category = HistoryCategory.OCCASIONAL
                else:
                    self._history.category = HistoryCategory.NEW
            else:
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

    def _show_user_feedback(
        self,
        action: str,
        description: str,
        feedback_type: FeedbackType,
        timeout: float = 1.5,
    ) -> None:
        """
        Display temporary feedback to the user in the UI.

        Shows a notification to the user about actions taken, such as playback
        changes, volume adjustments, or errors. The feedback is displayed
        for a configurable timeout period.

        Args:
            action: Short name of the action (e.g., "Play", "Volume")
            description: Longer description of what happened
            feedback_type: Category of feedback for styling (PLAYBACK, NAVIGATION, etc.)
            timeout: How long to show the feedback in seconds
        """
        should_show_feedback = (
            True
            if SETTINGS.appearance_settings.user_feedback_visible == "yes"
            else False
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
        """
        Safely check if the player is currently in paused state.

        Uses property access with fallback to state checking for reliability.

        Returns:
            True if player is paused, False otherwise
        """
        try:
            paused = self._safe_get_property("pause", False)
            return bool(paused)
        except Exception as e:
            logger.debug(f"Could not access pause property: {e}")
            return self._state.playback_state == PlaybackState.PAUSED

    def _safe_get_property(self, name: str, default=None):
        """
        Safely retrieve an MPV property with robust error handling.

        Provides a reliable way to access MPV properties even when the player
        is shutting down or in an unstable state. Returns a default value
        if the property cannot be accessed for any reason.

        Args:
            name: The name of the property to retrieve
            default: Value to return if property access fails

        Returns:
            The property value or the default if access fails
        """
        try:
            if hasattr(self, "_core_shutdown") and self._core_shutdown:
                return default

            if self._state.stop_requested:
                return default

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

        Safely handles boundary conditions to ensure the new position remains within
        valid playlist indices. Shows user feedback about the jump operation or
        any errors that occur.

        Args:
            jump_amount: Number of tracks to jump (positive for forward, negative for backward)
        """
        try:
            current_pos = self._state.current_playlist_pos
            new_pos = current_pos + jump_amount

            playlist_length = len(self._current_song_names)
            if playlist_length <= 0:
                return

            new_pos = max(0, min(new_pos, playlist_length - 1))

            if new_pos != current_pos:
                logger.debug(f"Jumping from position {current_pos} to {new_pos}")
                self._state.current_playlist_pos = new_pos
                self.playlist_play_index(new_pos)
        except Exception as e:
            logger.error(f"Error executing playlist jump: {e}")
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
            volume: Volume level (Default: 0-130)
        """
        self.volume = max(0, min(SETTINGS.maximum_volume, volume))
        logger.debug(f"Volume set to {self.volume}")

    def terminate(self):
        """Properly terminate the player, shutting down MPV gracefully."""
        try:
            self._state.stop_requested = True
            self._state.playback_state = PlaybackState.STOPPED

            if hasattr(self, "_thread_pool") and self._thread_pool:
                self._thread_pool.shutdown(wait=False)

            super().terminate()
        except Exception as e:
            logger.error(f"Error terminating player: {e}")

    def quit(self, code=None):
        """Override quit to ensure clean shutdown."""
        try:
            self._state.stop_requested = True
            self._state.playback_state = PlaybackState.STOPPED

            super().quit(code)
        except Exception as e:
            logger.error(f"Error quitting player: {e}")

    def __del__(self):
        """Ensure proper cleanup of resources when object is garbage collected."""
        self.cleanup_resources()

    def cleanup_resources(self):
        """Properly clean up all resources to prevent memory leaks."""
        try:
            if (
                hasattr(self, "_lyrics")
                and self._lyrics.future
                and not self._lyrics.future.done()
            ):
                self._lyrics.future.cancel()

            if hasattr(self, "_thread_pool") and self._thread_pool:
                try:
                    self._thread_pool.__exit__(None, None, None)
                except Exception as e:
                    logger.debug(f"Error shutting down thread pool: {e}")

            try:
                if hasattr(self, "_observers"):
                    for observer in self._observers:
                        observer.unregister()
                    self._observers = []
            except Exception as e:
                logger.debug(f"Error unregistering observers: {e}")
        except Exception as e:
            logger.error(f"Error during resource cleanup: {e}")

        try:
            super().__del__()
        except Exception:
            pass
