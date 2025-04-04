"""
MPV Player Module

This module provides an enhanced MPV player with rich UI, lyrics integration,
and proper integration with the unified database structure.
"""

import os
import time
import locale
import logging
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor
from rich.box import HEAVY
from rich.live import Live
from rich.panel import Panel
from rich.console import Group
from rich.progress import TextColumn, BarColumn, Progress

from . import python_mpv as mpv
from .python_mpv import ShutdownError
from .lyrics_handler import LyricsHandler
from ..utils.exceptions import DisplayError
from ..player.history import RecentlyPlayedManager
from ..utils.console_manager import (
    get_console,
    change_theme,
    get_available_themes,
    get_current_theme,
)
from ..utils.gradient_utils import (
    apply_gradient_to_text,
    create_subtle_gradient_text,
    get_gradient_style,
)

logger = logging.getLogger(__name__)


class MPVPlayer(mpv.MPV):
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
        volume: int = 100,
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
        self.console = get_console()  # Use our console manager
        self.lyrics_handler = LyricsHandler()
        self._thread_pool = ThreadPoolExecutor(max_workers=2)
        self.history_manager = RecentlyPlayedManager()  # Add history manager

        # UI state
        self._show_lyrics = False
        self._is_playing = False
        self._stop_requested = False
        self._elapsed_time: float = 0
        self._current_refresh_rate: float = 0.25
        self._current_theme: str = None  # Track current theme

        # Playlist state
        self._current_playlist_pos: int = 0
        self._current_song_names: List[str] = []
        self._queue_start_index: int = 0
        self._metadata_ready = False
        self._lyrics_future = None
        self._cached_lyrics = None

        # Action feedback
        self._user_action_feedback: Optional[Dict[str, Any]] = None
        self._user_feedback_timeout: float = 0

        # Metadata
        self._metadata: Dict[str, Any] = {
            "title": "Unknown",
            "artist": "Unknown",
            "album": "Unknown",
            "duration": 0,
        }

        # Set initial volume
        self.volume = volume

        # Configure MPV settings
        self._set_property("msg-level", f"all={loglevel}")
        self._set_property("audio-buffer", 2.0)  # Increase buffer size
        self._set_property("cache", "yes")  # Enable cache

        # Set up property observers and key bindings
        self._setup_property_observers()
        self._setup_key_bindings()

        # History integration
        self._play_count = 1
        self._last_played = None
        self._history_loaded = False

    # --- Property Observers ---

    def _setup_property_observers(self) -> None:
        """Set up observers for MPV player properties."""
        self.observe_property("pause", self._on_pause_change)
        self.observe_property("duration", self._on_duration_change)
        self.observe_property("metadata", self._on_metadata_change)
        self.observe_property("playlist-pos", self._on_playlist_pos_change)

        # Track playback position
        @self.property_observer("time-pos")
        def _track_time_pos(_name: str, value: Optional[float]) -> None:
            self._elapsed_time = value if value is not None else 0

    def _on_pause_change(self, _name: str, value: Optional[bool]) -> None:
        """
        Handle pause property changes.

        Args:
            _name: Property name
            value: New pause state
        """
        if value is None:
            return

        status = "Paused" if value else "Playing"
        logger.debug(f"Playback state changed to {status}")

        # Adjust refresh rate based on playback state
        self._current_refresh_rate = 1.0 if value else 0.25

        # Show user feedback
        self._show_user_feedback(
            "Pause" if value else "Play", f"Playback {status.lower()}"
        )

    def _on_duration_change(self, _name: str, value: Optional[float]) -> None:
        """
        Handle duration property changes.

        Args:
            _name: Property name
            value: New duration in seconds
        """
        if value and value > 0:
            self._metadata["duration"] = value
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
            if field in value and value[field] != self._metadata.get(field):
                self._metadata[field] = value[field]
                changed = True

        # Special handling for streaming metadata
        if "icy-title" in value and "title" not in value:
            icy_title = value["icy-title"]
            if " - " in icy_title:
                artist, title = icy_title.split(" - ", 1)
                self._metadata["artist"] = artist
                self._metadata["title"] = title
                changed = True
            else:
                self._metadata["title"] = icy_title
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

        old_pos = self._current_playlist_pos
        self._current_playlist_pos = value
        logger.debug(f"Playlist position changed from {old_pos} to {value}")

        # Reset metadata and lyrics for new song
        self._metadata_ready = False
        self._cached_lyrics = None
        self._history_loaded = False  # Reset history data

        # Cancel any pending lyrics fetch
        if self._lyrics_future and not self._lyrics_future.done():
            self._lyrics_future.cancel()

        # Show user feedback for track change
        song_name = self._current_song_names[value]
        self._show_user_feedback("Track Change", f"Playing: {song_name}")

        # Log when transitioning between history and searched songs
        if value == self._queue_start_index and self._queue_start_index > 0:
            logger.info("Now playing first searched song (after history)")
        elif value == 0 and self._queue_start_index > 0:
            logger.info("Now playing from history songs")

    # --- Key Bindings ---

    def _setup_key_bindings(self) -> None:
        """Set up keyboard controls for the player."""

        # Quit handler
        @self.on_key_press("q")
        def _quit() -> None:
            self._show_user_feedback("Quit", "Exiting player")
            self._stop_requested = True
            self.quit()

        # Volume control
        @self.on_key_press("UP")
        def _volume_up() -> None:
            new_volume = min(130, self.volume + 5)
            self.volume = new_volume
            self._show_user_feedback("Volume", f"Increased to {new_volume}%")

        @self.on_key_press("DOWN")
        def _volume_down() -> None:
            new_volume = max(0, self.volume - 5)
            self.volume = new_volume
            self._show_user_feedback("Volume", f"Decreased to {new_volume}%")

        # Playlist navigation
        @self.on_key_press("b")
        def _prev_track() -> None:
            self._show_user_feedback("Previous", "Playing previous track")
            self.playlist_prev()

        @self.on_key_press("n")
        def _next_track() -> None:
            self._show_user_feedback("Next", "Playing next track")
            self.playlist_next()

        # Toggle lyrics display
        @self.on_key_press("l")
        def _toggle_lyrics() -> None:
            self._show_lyrics = not self._show_lyrics
            action = "Showing" if self._show_lyrics else "Hiding"
            self._show_user_feedback("Lyrics", f"{action} lyrics display")

        # Seeking
        @self.on_key_press("RIGHT")
        def _seek_forward() -> None:
            self.seek(10)
            self._show_user_feedback("Seek", "Forward 10s")

        @self.on_key_press("LEFT")
        def _seek_backward() -> None:
            self.seek(-10)
            self._show_user_feedback("Seek", "Backward 10s")

        # Jump mode for playlist navigation
        self._jump_mode = False
        self._jump_number = ""

        # Single handler for all number keys
        def _handle_number_key(key: str) -> None:
            self._jump_mode = True
            self._jump_number += key
            self._show_user_feedback(
                "Jump Mode", f"Jump {self._jump_number} tracks, press n/b"
            )

        # Register the number key handlers with proper argument handling
        for digit in "0123456789":
            # Accept all 5 args passed by mpv but only use the digit we care about
            self.register_key_binding(
                digit,
                lambda _state,
                _name,
                _char,
                _scale,
                _arg,
                digit=digit: _handle_number_key(digit),
            )

        # Modified next and previous handlers to work with jump mode
        @self.on_key_press("n")
        def _next_track() -> None:
            if self._jump_mode:
                try:
                    jump_amount = int(self._jump_number) if self._jump_number else 1
                    self._execute_playlist_jump(jump_amount)
                    self._show_user_feedback("Jump", f"Forward {jump_amount} tracks")
                except ValueError:
                    self._show_user_feedback("Error", "Invalid jump number")
                finally:
                    self._jump_mode = False
                    self._jump_number = ""
            else:
                self._show_user_feedback("Next", "Playing next track")
                self.playlist_next()

        @self.on_key_press("b")
        def _prev_track() -> None:
            if self._jump_mode:
                try:
                    jump_amount = int(self._jump_number) if self._jump_number else 1
                    self._execute_playlist_jump(-jump_amount)
                    self._show_user_feedback("Jump", f"Backward {jump_amount} tracks")
                except ValueError:
                    self._show_user_feedback("Error", "Invalid jump number")
                finally:
                    self._jump_mode = False
                    self._jump_number = ""
            else:
                self._show_user_feedback("Previous", "Playing previous track")
                self.playlist_prev()

        # Add escape key to cancel jump mode
        @self.on_key_press("ESC")
        def _cancel_jump_mode() -> None:
            if self._jump_mode:
                self._jump_mode = False
                self._jump_number = ""
                self._show_user_feedback("Jump Mode", "Cancelled")

        # Theme cycling - updated to ensure theme name is properly tracked
        @self.on_key_press("t")
        def _cycle_theme() -> None:
            available_themes = get_available_themes()
            # Get current theme from console_manager
            current_theme = get_current_theme()

            # Find the current theme index
            try:
                current_index = available_themes.index(current_theme)
                # Get the next theme (wrapping around)
                next_index = (current_index + 1) % len(available_themes)
                next_theme = available_themes[next_index]

                # Change to the next theme
                change_theme(next_theme)
                self._current_theme = next_theme

                # Force cache reset for any theme-dependent elements
                self._cached_lyrics = None

                self._show_user_feedback("Theme", f"Changed to {next_theme}")
            except ValueError:
                # If the current theme isn't found in the list, start with first theme
                next_theme = available_themes[0]
                change_theme(next_theme)
                self._current_theme = next_theme

                # Force cache reset
                self._cached_lyrics = None

                self._show_user_feedback("Theme", f"Changed to {next_theme}")

    # --- Main Player API ---

    def player(
        self,
        queue: List[str],
        song_names: List[str],
        show_lyrics: bool = True,
        start_index: int = 0,
        file_paths: Optional[List[str]] = None,
    ) -> int:
        """
        Main entry point for playing media with enhanced UI.

        Args:
            queue: List of URLs to play
            song_names: List of song names corresponding to the URLs
            show_lyrics: Whether to show lyrics
            start_index: Index in the queue to start from (for history integration)
            file_paths: Optional list of local file paths (prioritized over URLs)

        Returns:
            Result code (0 for success)
        """
        # Initialize playback state
        self._stop_requested = False
        self._is_playing = True
        self._show_lyrics = show_lyrics
        self._current_song_names = song_names.copy()
        self._queue_start_index = start_index
        self._file_paths = file_paths or [""] * len(queue)

        try:
            # Log playback information
            logger.info(
                f"Playing queue with {len(queue)} songs, starting at {start_index}"
            )
            local_files_count = sum(1 for path in self._file_paths if path)
            if local_files_count > 0:
                logger.info(f"Using {local_files_count} local files for playback")

            # Set up queue and start playback
            self._initialize_player(queue, start_index)

            # Start display
            first_song = (
                song_names[start_index]
                if 0 <= start_index < len(song_names)
                else "Unknown"
            )
            self._start_display(first_song)

            # Wait for playback to complete
            if self.playlist_count:
                self.wait_for_playback()

            return 0

        except KeyboardInterrupt:
            self.console.print("\n[yellow]Playback interrupted by user[/]")
            return 1
        except Exception as e:
            logger.error(f"Error during playback: {e}", exc_info=True)
            self.console.print(f"[bold red]Playback error: {str(e)}[/]")
            return 2
        finally:
            # Clean up resources
            self._stop_display()
            if self._thread_pool:
                self._thread_pool.shutdown(wait=False)

    def _initialize_player(self, queue: List[str], start_index: int = 0) -> None:
        """
        Initialize player with queue and start playback.

        Args:
            queue: List of URLs to play
            start_index: Index to start playback from
        """
        # Add all items to the playlist, prioritizing local files over URLs
        for i, url in enumerate(queue):
            # Check if we have a local file path for this song
            local_path = ""
            if hasattr(self, "_file_paths") and i < len(self._file_paths):
                local_path = self._file_paths[i]

            if local_path and os.path.exists(local_path):
                # Use local file (directly, without youtube-dl)
                logger.info(f"Using local file for playback: {local_path}")
                self.playlist_append(local_path)
            elif url and url.strip():  # Ensure URL is not empty
                # Use URL (will be processed through youtube-dl)
                logger.info(f"Using URL for playback: {url}")
                self.playlist_append(url)
            else:
                # If both are empty, log error
                logger.error(f"No valid URL or file path for song at position {i}")
                # Add a placeholder to maintain playlist ordering
                self.playlist_append("null://")

        # Set the starting position
        logger.info(f"Starting playback at index {start_index}")
        self._current_playlist_pos = start_index
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
        self._stop_requested = True

    def _run_display(self, song_name: str) -> None:
        """
        Run the live display UI showing playback information and controls.

        Args:
            song_name: The initial song name to display
        """
        try:
            # Define control key information
            controls_text = (
                "[white][bold cyan]Space[/]:Pause · "
                "[bold cyan]q[/]:Quit · "
                "[bold cyan]b[/]:Prev · "
                "[bold cyan]n[/]:Next · "
                "[bold cyan]←→[/]:Seek · "
                "[bold cyan]↑↓[/]:Volume · "
                "[bold cyan]l[/]:Lyrics · "
                "[bold cyan]t[/]:Theme[/]"
            )

            # Initialize display state
            last_song = None
            metadata_ready = False
            refresh_count = 0

            # Create the live display using our console from the manager
            with Live(
                refresh_per_second=4, console=self.console, transient=True
            ) as live:
                while not self._stop_requested and self._is_playing:
                    try:
                        # Current position and song info
                        current_song = self._get_current_song_name()
                        elapsed = self._elapsed_time or 0
                        duration = self._metadata.get("duration", 0)
                        artist = self._metadata.get("artist", "Unknown")
                        album = self._metadata.get("album", "Unknown")

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
                            metadata_ready = self._metadata_ready

                        # Process lyrics if enabled
                        lyrics_section = ""
                        if self._show_lyrics:
                            lyrics_section = self._get_lyrics_display(
                                current_song,
                                artist,
                                album,
                                elapsed,
                                duration,
                                metadata_ready,
                            )

                        # Create the content for display
                        content = self._create_display_content(
                            current_song,
                            artist,
                            album,
                            elapsed,
                            duration,
                            lyrics_section,
                        )

                        # Create panel with user feedback if available
                        panel = Panel(
                            content,
                            title="♫ Aurras Music Player ♫",
                            border_style="cyan",
                            box=HEAVY,
                            padding=(0, 1),
                            subtitle=controls_text,
                            subtitle_align="right",
                        )
                        # Update the display
                        live.update(panel)

                        # Apply appropriate refresh rate
                        time.sleep(self._current_refresh_rate)

                    except ShutdownError:
                        # Handle mpv shutdown gracefully
                        self._stop_requested = True
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
        # Check if we have meaningful metadata
        title = self._metadata.get("title", "Unknown")
        artist = self._metadata.get("artist", "Unknown")
        duration = self._metadata.get("duration", 0)

        # Consider metadata ready if we have at least title and duration
        metadata_complete = title != "Unknown" and duration > 0

        # If metadata becomes complete and wasn't before, trigger lyrics lookup
        if metadata_complete and not self._metadata_ready:
            self._metadata_ready = True
            song = title
            album = self._metadata.get("album", "Unknown")

            # Trigger async lyrics lookup if lyrics are enabled
            if self._show_lyrics and self.lyrics_handler.has_lyrics_support():
                logger.debug(f"Starting async lyrics lookup for '{song}'")
                self._prefetch_lyrics(song, artist, album, int(duration))

    def _prefetch_lyrics(
        self, song: str, artist: str, album: str, duration: int
    ) -> None:
        """
        Prefetch lyrics asynchronously in a background thread.

        Args:
            song: Song name
            artist: Artist name
            album: Album name
            duration: Song duration in seconds
        """
        # Skip if we already have cached lyrics
        if self._cached_lyrics:
            return

        # Define the fetch function
        def fetch_lyrics():
            try:
                # First check cache
                cached = self.lyrics_handler.get_from_cache(song, artist, album)
                if cached:
                    logger.debug(f"Found lyrics in cache for '{song}'")
                    return cached

                # If not in cache, fetch from service
                lyrics = self.lyrics_handler.fetch_lyrics(song, artist, album, duration)
                if lyrics:
                    logger.info(f"Successfully fetched lyrics for '{song}'")
                    # Store in cache
                    self.lyrics_handler.store_in_cache(lyrics, song, artist, album)
                    return lyrics
                else:
                    logger.info(f"No lyrics found for '{song}'")
                    return []
            except Exception as e:
                logger.error(f"Error fetching lyrics: {e}")
                return []

        # Launch the async fetch
        self._lyrics_future = self._thread_pool.submit(fetch_lyrics)

    def _get_lyrics_display(
        self,
        song: str,
        artist: str,
        album: str,
        elapsed: float,
        duration: float,
        metadata_ready: bool,
    ) -> str:
        """
        Get lyrics display content for the current song and playback position.

        Args:
            song: Song name
            artist: Artist name
            album: Album name
            elapsed: Current playback position in seconds
            duration: Song duration in seconds
            metadata_ready: Whether metadata is ready for lyrics fetch

        Returns:
            Formatted lyrics section as a string
        """
        # Header for lyrics section
        header = "\n\n[bold magenta]─── Lyrics ───[/bold magenta]\n"

        # If lyrics feature is not available
        if not self.lyrics_handler.has_lyrics_support():
            return (
                f"{header}[italic yellow]Lyrics feature not available[/italic yellow]"
            )

        # If metadata is not ready yet
        if not metadata_ready:
            return (
                f"{header}[italic yellow]Waiting for song metadata...[/italic yellow]"
            )

        # Check if we have cached lyrics from a previous fetch
        if self._cached_lyrics:
            # Format and display the lyrics with gradient effect
            lyrics_content = self.lyrics_handler.create_focused_lyrics_view(
                self._cached_lyrics, elapsed, song, artist, album
            )
            return f"{header}{lyrics_content}"

        # Check if we have results from the async fetch
        if self._lyrics_future and self._lyrics_future.done():
            try:
                lyrics = self._lyrics_future.result()
                if lyrics:
                    self._cached_lyrics = lyrics
                    lyrics_content = self.lyrics_handler.create_focused_lyrics_view(
                        lyrics, elapsed, song, artist, album
                    )
                    return f"{header}{lyrics_content}"
                else:
                    return f"{header}[italic yellow]No lyrics available for this song[/italic yellow]"
            except Exception as e:
                logger.error(f"Error retrieving lyrics: {e}")
                return f"{header}[italic red]Error: {str(e)}[/italic red]"

        # Async fetch is still in progress
        if self._lyrics_future and not self._lyrics_future.done():
            return f"{header}[italic]Fetching lyrics...[/italic]"

        # No fetch in progress and no cached lyrics
        return (
            f"{header}[italic yellow]No lyrics available for this song[/italic yellow]"
        )

    def _create_display_content(
        self,
        song: str,
        artist: str,
        album: str,
        elapsed: float,
        duration: float,
        lyrics_section: str,
    ) -> Group:
        """
        Create the content for the player UI display.

        Args:
            song: Song name
            artist: Artist name
            album: Album name
            elapsed: Current playback position in seconds
            duration: Song duration in seconds
            lyrics_section: Formatted lyrics content

        Returns:
            Rich Group containing the formatted display content
        """
        # Load history data if needed
        if not self._history_loaded:
            self._load_history_data(song)

        # Format song information with history
        source = self._get_song_source()
        info_text = self._format_song_info(song, artist, album, source)

        # Create progress bar
        progress = self._create_progress_bar(elapsed, duration)

        # Get status text
        status_text = self._get_status_text()

        # Add history information
        history_text = self._get_history_text(song)

        # Get user feedback if available
        user_feedback = self._get_user_feedback_text()

        # Combine elements into a group
        elements = [info_text, progress, status_text]

        # Add history text if available
        if history_text:
            elements.append(history_text)

        # Add user feedback if available
        if user_feedback:
            elements.append(user_feedback)

        # Add lyrics if enabled
        if self._show_lyrics and lyrics_section:
            elements.append(lyrics_section)

        return Group(*elements)

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
                self._play_count = song_data.get("play_count", 1)
                self._last_played = song_data.get("played_at", 0)
            else:
                # If not found in history, reset values
                self._play_count = 0
                self._last_played = None

            self._history_loaded = True
            logger.debug(f"Loaded history for '{song_name}': count={self._play_count}")

        except Exception as e:
            logger.error(f"Error loading history data: {e}")
            self._play_count = 0
            self._last_played = None
            self._history_loaded = (
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
        if not self._history_loaded or self._play_count <= 1:
            return None

        # Format the play count with appropriate styling
        if self._play_count > 10:
            count_text = (
                f"[bold gold1]You've played this {self._play_count} times![/bold gold1]"
            )
        elif self._play_count > 5:
            count_text = f"[yellow]You've played this {self._play_count} times[/yellow]"
        elif self._play_count > 1:
            count_text = f"[dim]You've played this {self._play_count} times[/dim]"
        else:
            return None

        # Format the last played info if available
        last_played_text = ""
        if self._last_played:
            current_time = int(time.time())
            time_diff = current_time - self._last_played

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
        self, action: str, description: str, timeout: float = 1.5
    ) -> None:
        """
        Show user feedback for an action in the UI.

        Args:
            action: Short name of the action
            description: Longer description of what happened
            timeout: How long to show the feedback (seconds)
        """
        self._user_action_feedback = {
            "action": action,
            "description": description,
            "timestamp": time.time(),
        }
        self._user_feedback_timeout = timeout

    def _get_user_feedback_text(self) -> Optional[str]:
        """
        Get formatted user feedback text if available and not expired.

        Returns:
            Formatted feedback text or None if no feedback to show
        """
        if not self._user_action_feedback:
            return None

        # Check if feedback has expired
        elapsed = time.time() - self._user_action_feedback["timestamp"]
        if elapsed > self._user_feedback_timeout:
            self._user_action_feedback = None
            return None

        # Format the feedback
        action = self._user_action_feedback["action"]
        description = self._user_action_feedback["description"]
        return f"\n[bold cyan]► {action}:[/bold cyan] [white]{description}[/white]"

    # --- Utility Methods ---

    def _get_current_song_name(self) -> str:
        """Get the name of the currently playing song."""
        if 0 <= self._current_playlist_pos < len(self._current_song_names):
            return self._current_song_names[self._current_playlist_pos]
        return "Unknown"

    def _get_song_source(self) -> str:
        """Get the source indicator for the current song (history or searched)."""
        source_text = ""

        # Check if song is from history
        if (
            self._current_playlist_pos < self._queue_start_index
            and self._queue_start_index > 0
        ):
            source_text = " [dim](From History)[/dim]"

        # Check if song is from local file
        if hasattr(self, "_file_paths") and 0 <= self._current_playlist_pos < len(
            self._file_paths
        ):
            if self._file_paths[self._current_playlist_pos]:
                source_text += " [green dim](Local File)[/green dim]"

        return source_text

    def _format_song_info(self, song: str, artist: str, album: str, source: str) -> str:
        """Format song information for display with subtle gradients."""
        # Get the gradient style for the current theme
        style = get_gradient_style()

        # Start with song name using title gradient
        info_text = f"[bold green]Now Playing:[/] {apply_gradient_to_text(song, 'title', bold=True)}{source}"

        # Add artist if available with artist gradient
        if artist != "Unknown" and artist.strip():
            artist_text = apply_gradient_to_text(artist, "artist")
            info_text += f"\n[bold magenta]Artist:[/] {artist_text}"

        # Add album if available
        if album != "Unknown" and album.strip():
            album_text = create_subtle_gradient_text(album, "artist")
            info_text += f" [dim]·[/] [bold magenta]Album:[/] {album_text}"

        # Add position information
        position_info = f"[dim]Song {self._current_playlist_pos + 1} of {len(self._current_song_names)}[/dim]"
        info_text += f"\n{position_info}"

        return info_text

    def _get_history_text(self, song_name: str) -> Optional[str]:
        """
        Get formatted history information text with subtle gradients.

        Args:
            song_name: Name of the current song

        Returns:
            Formatted history text or None if not available
        """
        if not self._history_loaded or self._play_count <= 1:
            return None

        # Format the play count with appropriate styling and gradients
        style = get_gradient_style()

        if self._play_count > 10:
            count_text = apply_gradient_to_text(
                f"You've played this {self._play_count} times!", "history", bold=True
            )
        elif self._play_count > 5:
            count_text = apply_gradient_to_text(
                f"You've played this {self._play_count} times", "history"
            )
        elif self._play_count > 1:
            count_text = f"[dim]You've played this {self._play_count} times[/dim]"
        else:
            return None

        # Format the last played info if available
        last_played_text = ""
        if self._last_played:
            current_time = int(time.time())
            time_diff = current_time - self._last_played

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
        self, action: str, description: str, timeout: float = 1.5
    ) -> None:
        """
        Show user feedback for an action in the UI.

        Args:
            action: Short name of the action
            description: Longer description of what happened
            timeout: How long to show the feedback (seconds)
        """
        self._user_action_feedback = {
            "action": action,
            "description": description,
            "timestamp": time.time(),
        }
        self._user_feedback_timeout = timeout

    def _get_user_feedback_text(self) -> Optional[str]:
        """
        Get formatted user feedback text with gradient effect.

        Returns:
            Formatted feedback text or None if no feedback to show
        """
        if not self._user_action_feedback:
            return None

        # Check if feedback has expired
        elapsed = time.time() - self._user_action_feedback["timestamp"]
        if elapsed > self._user_feedback_timeout:
            self._user_action_feedback = None
            return None

        # Format the feedback with gradients
        action = self._user_action_feedback["action"]
        description = self._user_action_feedback["description"]

        # Apply gradients based on the current theme
        styled_action = apply_gradient_to_text(action, "feedback", bold=True)
        styled_description = create_subtle_gradient_text(description, "feedback")

        return f"\n► {styled_action}: {styled_description}"

    def _get_status_text(self) -> str:
        """
        Get the current player status text with subtle gradient effects.

        Returns:
            Formatted status text
        """
        try:
            status = "Paused" if self.pause else "Playing"
            vol = self.volume
            theme_info = (
                f" · Theme: {self._current_theme}" if self._current_theme else ""
            )

            # Apply subtle gradient to the status text
            status_text = create_subtle_gradient_text(
                f"Status: {status} · Volume: {vol}%{theme_info}", "status"
            )
            return f"[dim]{status_text}[/dim]"
        except ShutdownError:
            self._stop_requested = True
            return "[dim]Status: Stopped[/dim]"
        except Exception:
            return "[dim]Status: Unknown[/dim]"

    def _create_progress_bar(self, elapsed: float, duration: float) -> Progress:
        """
        Create a progress bar for song playback with gradient effect.

        Args:
            elapsed: Current playback position in seconds
            duration: Song duration in seconds

        Returns:
            Rich Progress object
        """
        # Get theme colors for progress
        style = get_gradient_style()
        progress_colors = style.get("progress", ["cyan", "green"])

        # Use the first color for the bar and the second for completed sections
        bar_color = progress_colors[0]
        complete_color = progress_colors[-1]

        progress = Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40, style=bar_color, complete_style=complete_color),
            TextColumn("[bold cyan]{task.fields[time]} / {task.fields[duration]}"),
        )

        # Get playback status text
        try:
            play_status = "[red] PAUSED[/red]" if self.pause else " PLAYING"
        except ShutdownError:
            play_status = " STOPPED"
            self._stop_requested = True

        # Add task to progress
        progress.add_task(
            f"[bold]{play_status}[/]",
            total=100,
            completed=min(
                100, max(0, (elapsed / duration) * 100 if duration > 0 else 0)
            ),
            time=self._format_time(elapsed),
            duration=self._format_time(duration),
        )

        return progress

    def _format_time(self, seconds: float) -> str:
        """Format time in seconds to MM:SS format."""
        if seconds is None or seconds < 0:
            return "0:00"
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}:{secs:02d}"

    # --- Public API ---

    def get_playback_info(self) -> Dict[str, Any]:
        """
        Get current playback information.

        Returns:
            Dictionary with playback state, position, duration, volume and metadata
        """
        try:
            return {
                "is_playing": not self.pause,
                "position": self.time_pos or 0,
                "duration": self.duration or 0,
                "volume": self.volume,
                "metadata": self._metadata.copy(),
                "playlist_position": self._current_playlist_pos,
                "playlist_count": len(self._current_song_names),
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
            }

    def set_volume(self, volume: int) -> None:
        """
        Set the player volume.

        Args:
            volume: Volume level (0-130)
        """
        self.volume = max(0, min(130, volume))
        logger.debug(f"Volume set to {self.volume}")


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
        file_paths: Optional[List[str]] = None,
    ) -> int:
        """Play a list of songs with the given URLs."""
        return self.player.player(
            queue=urls,
            song_names=songs,
            show_lyrics=show_lyrics,
            start_index=start_index,
            file_paths=file_paths,
        )
