"""MPV player with enhanced UI and functionality."""

import time
import locale
import logging
import threading
import re
from typing import Dict, Any, List, Optional, Tuple

from rich.console import Console, Group
from rich.panel import Panel
from rich.live import Live
from rich.progress import TextColumn, BarColumn, Progress
from rich.box import ROUNDED, HEAVY, HORIZONTALS

from . import python_mpv as mpv
from .python_mpv import ShutdownError
from .lyrics_handler import LyricsHandler

from ..utils.exceptions import DisplayError, LyricsError

logger = logging.getLogger(__name__)


class MPVError(Exception):
    """Custom exception for MPV-related errors."""

    pass


class MPVPlayer(mpv.MPV):
    """
    Enhanced MPV player with better UI and extended functionality.

    This class extends the base MPV player with rich UI, history integration,
    improved keyboard controls, and metadata handling.

    Attributes:
        console: Rich console for beautiful output
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
        Initialize the enhanced MPV player with customized settings.

        Args:
            ytdl: Whether to enable YouTube-DL integration
            ytdl_format: Format string for YouTube-DL
            volume: Initial volume level (0-130)
            loglevel: Logging level for MPV messages
        """
        # Set locale to ensure proper number formatting
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

        # Initialize instance variables
        self.console = Console()
        # Initialize lyrics handler
        self.lyrics_handler = LyricsHandler()
        self._reset_metadata_ready_flag = False
        self._is_playing = False
        self._stop_requested = False
        self._display_thread: Optional[threading.Thread] = None
        self._progress_thread: Optional[threading.Thread] = None
        self._progress_instance = None
        self._elapsed_time: float = 0
        self._current_playlist_pos: int = 0
        self._current_song_names: List[str] = []
        self._history_song_count: int = 0
        self._queue_start_index: int = 0
        self._show_lyrics = False  # New flag to control lyrics visibility

        # UI feedback state
        self._user_action_feedback: Optional[Dict[str, Any]] = None
        self._user_feedback_timeout: float = 0

        # Refresh rate configuration
        self._default_refresh_rate: float = 0.25
        self._paused_refresh_rate: float = 1.0
        self._current_refresh_rate: float = self._default_refresh_rate

        # Set initial volume
        self.volume = volume

        # Set up property observers
        self._setup_property_observers()

        # Initialize metadata
        self._metadata: Dict[str, Any] = {
            "title": "Unknown",
            "artist": "Unknown",
            "album": "Unknown",
            "duration": 0,
        }

        # Set message level
        try:
            self._set_property("msg-level", f"all={loglevel}")
        except Exception as e:
            logger.warning(f"Failed to set message level: {e}")

        # Set up key bindings
        self._setup_key_bindings()

    # --- Event handlers and setup methods ---

    def _setup_property_observers(self) -> None:
        """Set up observers for MPV properties."""
        # Observe various properties to react to changes
        self.observe_property("pause", self._on_pause_change)
        self.observe_property("duration", self._on_duration_change)
        self.observe_property("metadata", self._on_metadata_change)
        self.observe_property("playlist-pos", self._on_playlist_pos_change)

        # Time position observer for tracking playback progress
        @self.property_observer("time-pos")
        def _get_elapsed_time(_name: str, value: Optional[float]) -> None:
            self._elapsed_time = value if value is not None else 0

    def _setup_key_bindings(self) -> None:
        """Set up key bindings for controlling playback."""

        # Quit handler
        @self.on_key_press("q")
        def _quit_event() -> None:
            self._show_user_feedback("Quit", "Exiting player")
            self._handle_quit()

        # Volume control
        @self.on_key_press("UP")
        def _volume_up_event() -> None:
            self._handle_volume_up_event()

        @self.on_key_press("DOWN")
        def _volume_down_event() -> None:
            self._handle_volume_down_event()

        # Playlist navigation
        @self.on_key_press("b")
        def _play_previous() -> None:
            logger.debug("Previous key pressed")
            self._show_user_feedback("Previous", "Playing previous track")
            self.playlist_prev()

        @self.on_key_press("n")
        def _play_next() -> None:
            logger.debug("Next key pressed")
            self._show_user_feedback("Next", "Playing next track")
            self.playlist_next()

        # Toggle lyrics display
        @self.on_key_press("l")
        def _toggle_lyrics() -> None:
            self._toggle_lyrics_display()

        # Seek forward/backward
        @self.on_key_press("RIGHT")
        def _seek_forward() -> None:
            try:
                self.seek(10)
                self._show_user_feedback("Seek", "Forward 10s")
            except Exception as e:
                logger.error(f"Error seeking forward: {e}")

        @self.on_key_press("LEFT")
        def _seek_backward() -> None:
            try:
                self.seek(-10)
                self._show_user_feedback("Seek", "Backward 10s")
            except Exception as e:
                logger.error(f"Error seeking backward: {e}")

    def _toggle_lyrics_display(self) -> None:
        """Toggle lyrics display on/off."""
        self._show_lyrics = not self._show_lyrics
        action = "Showing" if self._show_lyrics else "Hiding"
        self._show_user_feedback("Lyrics", f"{action} lyrics display")
        logger.debug(f"Lyrics display toggled: {self._show_lyrics}")

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
        logger.debug(f"User action: {action} - {description}")

    def _on_playlist_pos_change(self, name: str, value: Optional[int]) -> None:
        """
        Handle changes in playlist position.

        Args:
            name: Property name
            value: New playlist position
        """
        if value is not None and 0 <= value < len(self._current_song_names):
            old_pos = self._current_playlist_pos
            self._current_playlist_pos = value
            logger.debug(f"Playlist position changed from {old_pos} to {value}")

            # Reset metadata_ready flag when changing songs
            self._reset_metadata_ready_flag = True

            # Show user feedback
            song_name = (
                self._current_song_names[value]
                if 0 <= value < len(self._current_song_names)
                else "Unknown"
            )
            self._show_user_feedback("Track Change", f"Playing: {song_name}")

            # Log when we transition between history and searched songs
            if value == self._queue_start_index:
                logger.info("Now playing first searched song")
            elif value == 0 and self._queue_start_index > 0:
                logger.info("Now playing from history songs")

    def _on_pause_change(self, name: str, value: Optional[bool]) -> None:
        """
        Handle pause property changes.

        Args:
            name: Property name
            value: New pause state
        """
        if value is not None:
            status = "Paused" if value else "Playing"
            logger.debug(f"Playback state changed to {status}")

            # Adjust refresh rate based on playback state
            if value:  # Paused
                self._current_refresh_rate = self._paused_refresh_rate
                self._show_user_feedback("Pause", "Playback paused")
            else:  # Playing
                self._current_refresh_rate = self._default_refresh_rate
                self._show_user_feedback("Play", "Playback resumed")

    def _on_duration_change(self, name: str, value: Optional[float]) -> None:
        """
        Handle duration property changes.

        Args:
            name: Property name
            value: New duration in seconds
        """
        if value and value > 0:
            self._metadata["duration"] = value
            logger.debug(f"Duration updated to {value:.2f} seconds")

    def _on_metadata_change(self, name: str, value: Optional[Dict[str, Any]]) -> None:
        """
        Handle metadata changes.

        Args:
            name: Property name
            value: New metadata dictionary
        """
        if not value:
            return

        # Update simple metadata fields
        for field in ["title", "artist", "album"]:
            if field in value:
                self._metadata[field] = value[field]

        # Special handling for streaming metadata
        if "icy-title" in value and "title" not in value:
            icy_title = value["icy-title"]
            if " - " in icy_title:
                artist, title = icy_title.split(" - ", 1)
                self._metadata["artist"] = artist
                self._metadata["title"] = title
            else:
                self._metadata["title"] = icy_title

        logger.debug(f"Updated metadata: {self._metadata}")

    # --- UI Control Methods ---

    def _handle_volume_up_event(self) -> None:
        """Handle up arrow key event to increase volume."""
        new_volume = min(130, self.volume + 5)
        self.set_volume(new_volume)
        self._show_user_feedback("Volume", f"Increased to {new_volume}%")
        logger.debug(f"Volume increased to {new_volume}")

    def _handle_volume_down_event(self) -> None:
        """Handle down arrow key event to decrease volume."""
        new_volume = max(0, self.volume - 5)
        self.set_volume(new_volume)
        self._show_user_feedback("Volume", f"Decreased to {new_volume}%")
        logger.debug(f"Volume decreased to {new_volume}")

    def _handle_quit(self) -> None:
        """Handle quit key press."""
        self._stop_requested = True
        logger.info("Quit requested by user")

        # Clean up and quit
        self.quit()

    # --- Main Player Methods ---

    def player(
        self,
        queue: List[str],
        song_names: List[str],
        show_lyrics: bool = True,
        start_index: int = 0,  # Starting point in the queue
    ) -> int:
        """
        Play media with enhanced UI and functionality.

        Args:
            queue: List of song URLs to play
            song_names: List of song names corresponding to the URLs
            show_lyrics: Whether to show lyrics
            start_index: Index in the queue to start playback from (for history integration)

        Returns:
            Result code (0 for success)
        """
        # Initialize state
        self._stop_requested = False
        self._is_playing = True
        result_code = 0
        self._current_song_names = song_names.copy()
        self._queue_start_index = start_index
        self._history_song_count = start_index

        # Set lyrics display according to parameter - FIX: Was missing this line
        self._show_lyrics = show_lyrics
        logger.debug(f"Lyrics display initialized to: {self._show_lyrics}")

        # Log playback information
        logger.info(
            f"Playing queue with {len(queue)} songs: {self._history_song_count} history songs, "
            f"{len(queue) - self._history_song_count} searched songs"
        )
        logger.info(f"Starting playback at index {start_index}")

        try:
            # Setup and start playback
            self._initialize_player(queue, start_index)

            # Determine which song to display first
            first_song_name = (
                song_names[start_index]
                if 0 <= start_index < len(song_names)
                else "Unknown"
            )

            # Start UI display
            self._start_display(first_song_name)

            # Wait for playback to complete
            try:
                if self.playlist_count:
                    self.wait_for_playback()
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Playback interrupted by user[/]")
                result_code = 1

            return result_code

        except KeyboardInterrupt:
            self.console.print("\n[yellow]Playback interrupted by user[/]")
            return 1
        except Exception as e:
            logger.error(f"Error during playback: {e}")
            self.console.print(f"[bold red]Playback error: {str(e)}[/]")
            return 2
        finally:
            # Clean up resources
            self._cleanup_resources()

    def _cleanup_resources(self) -> None:
        """Clean up resources when playback is finished."""
        self._stop_display()

    def _initialize_player(self, queue: List[str], start_index: int = 0) -> None:
        """
        Initialize player with queue and start at specified index.

        Args:
            queue: List of URLs to play
            start_index: Index to start playback from
        """
        # First initialize the queue with all songs
        self._initialize_queue(queue)

        # Wait a moment for the queue to be fully loaded
        time.sleep(0.1)

        # Then start playback from the specified index
        if start_index > 0:
            logger.info(f"Setting playlist position to {start_index}")
            try:
                # Set the internal position first
                self._current_playlist_pos = start_index
                # Then tell MPV to play this position
                self.playlist_play_index(start_index)

                # Verify the position was set correctly
                time.sleep(0.1)  # Give MPV a moment to update
                actual_pos = self.playlist_pos
                if actual_pos is not None and actual_pos != start_index:
                    logger.warning(
                        f"Position mismatch: wanted {start_index}, got {actual_pos}. Retrying..."
                    )
                    self.playlist_play_index(start_index)
            except Exception as e:
                logger.error(f"Error setting initial playlist position: {e}")
        else:
            # Start from the beginning
            self.playlist_play_index(0)

        logger.debug(f"Starting playback at index {start_index}")

    def _initialize_queue(self, queue: List[str]) -> None:
        """
        Initialize the player's queue with the provided songs.

        Args:
            queue: List of URLs to add to the queue
        """
        for song in queue:
            self.playlist_append(song)
        logger.debug(f"Initialized queue with {len(queue)} songs")

    # --- Display Methods ---

    def _start_display(self, song_name: str) -> None:
        """
        Start a beautiful live display showing playback info and controls.

        Args:
            song_name: Name of the current song
        """
        self._run_display(song_name)

    def _stop_display(self) -> None:
        """Stop the display cleanly."""
        self._stop_requested = True
        if (
            hasattr(self, "_display_thread")
            and self._display_thread
            and self._display_thread.is_alive()
        ):
            try:
                self._display_thread.join(timeout=1.0)
            except Exception as e:
                logger.warning(f"Error stopping display thread: {e}")

    def _run_display(self, song_name: str) -> None:
        """
        Run the live display showing song information and playback status.

        Args:
            song_name: Name of the current song
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
                "[bold cyan]l[/]:Lyrics[/]"
            )

            # Initialize display state
            last_displayed_song = None
            last_playlist_pos = -1
            metadata_ready = False
            metadata_checked = False
            refresh_count = 0

            # Reset metadata flag
            self._reset_metadata_ready_flag = False

            # Wait a short moment before initial display to allow metadata to load
            time.sleep(0.5)

            # Create a live display that updates automatically
            with Live(
                refresh_per_second=4,  # Initial refresh rate
                console=self.console,
                transient=True,
            ) as live:
                while not self._stop_requested and self._is_playing:
                    try:
                        # Update display state
                        display_state = self._update_display_state(
                            last_displayed_song,
                            last_playlist_pos,
                            metadata_ready,
                            metadata_checked,
                            refresh_count,
                        )

                        # Unpack the updated state
                        current_song = display_state["current_song"]
                        artist = display_state["artist"]
                        album = display_state["album"]
                        elapsed = display_state["elapsed"]
                        duration = display_state["duration"]
                        metadata_ready = display_state["metadata_ready"]
                        last_playlist_pos = display_state["playlist_pos"]
                        metadata_checked = display_state["metadata_checked"]
                        refresh_count = display_state["refresh_count"]

                        # If song changed, update the last displayed song
                        if current_song != last_displayed_song:
                            last_displayed_song = current_song

                        # Process lyrics if enabled
                        lyrics_section = ""
                        if self._show_lyrics:
                            lyrics_section = self._process_lyrics_for_display(
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

                        # Create a panel with user feedback if available
                        panel = self._create_display_panel(content, controls_text)

                        # Update the display
                        live.update(panel)

                        # Adjust the refresh rate based on playback state
                        time.sleep(self._current_refresh_rate)

                    except ShutdownError:
                        # Handle mpv shutdown gracefully
                        self._stop_requested = True
                        logger.debug("MPV shutdown during display update")
                        break
                    except Exception as e:
                        # Log display errors but continue
                        logger.error(f"Display update error: {e}")
                        time.sleep(1.0)  # Longer sleep on error

        except Exception as e:
            logger.error(f"Display thread error: {e}")
            raise DisplayError(f"Display error: {e}")

    def _update_display_state(
        self,
        last_displayed_song: Optional[str],
        last_playlist_pos: int,
        metadata_ready: bool,
        metadata_checked: bool,
        refresh_count: int,
    ) -> Dict[str, Any]:
        """
        Update the display state based on current player state.

        Args:
            last_displayed_song: Previously displayed song name
            last_playlist_pos: Previous playlist position
            metadata_ready: Whether metadata is ready for lyrics fetch
            metadata_checked: Whether metadata has been checked
            refresh_count: Count of refresh cycles

        Returns:
            Dictionary with updated display state
        """
        # Get current playback position
        elapsed = self._elapsed_time or 0
        duration = self.duration or 0

        # Check if playlist position changed
        playlist_position_changed = last_playlist_pos != self._current_playlist_pos
        if playlist_position_changed:
            logger.debug(
                f"Display detected playlist position change: {last_playlist_pos} -> {self._current_playlist_pos}"
            )
            # Reset counters when changing songs
            refresh_count = 0
            metadata_checked = False

        # Handle metadata reset flag
        if self._reset_metadata_ready_flag:
            metadata_ready = False
            metadata_checked = False
            self._reset_metadata_ready_flag = False
            logger.debug("Reset metadata ready flag due to song change")

        # Track number of refresh cycles to allow metadata to load
        refresh_count += 1

        # Get metadata for display
        try:
            artist = self._metadata.get("artist", "Unknown")
            album = self._metadata.get("album", "Unknown")

            # Check if we have complete metadata
            if refresh_count > 5 and not metadata_checked:
                metadata_checked = True
                if duration > 0 and artist != "Unknown" and album != "Unknown":
                    metadata_ready = True
                    logger.debug("Metadata is ready for lyrics fetching")
                else:
                    logger.debug("Metadata not yet complete for lyrics fetching")

            # Check metadata periodically to see if it's been updated
            if refresh_count % 5 == 0 and not metadata_ready:
                if duration > 0 and artist != "Unknown" and album != "Unknown":
                    metadata_ready = True
                    logger.debug("Metadata is now ready for lyrics fetching")
                # If no metadata after 15 refreshes, try fetching with what we have
                elif refresh_count > 15:
                    logger.debug("Attempting lyrics fetch with incomplete metadata")
                    metadata_ready = True
        except Exception:
            artist = "Unknown"
            album = "Unknown"

        # Get current song name and source
        current_song = self._get_current_song_name()

        return {
            "current_song": current_song,
            "artist": artist,
            "album": album,
            "elapsed": elapsed,
            "duration": duration,
            "metadata_ready": metadata_ready,
            "playlist_pos": self._current_playlist_pos,
            "metadata_checked": metadata_checked,
            "refresh_count": refresh_count,
        }

    def _process_lyrics_for_display(
        self,
        song: str,
        artist: str,
        album: str,
        elapsed: float,
        duration: float,
        metadata_ready: bool,
    ) -> str:
        """
        Process lyrics for display.

        Args:
            song: Current song name
            artist: Artist name
            album: Album name
            elapsed: Current playback position in seconds
            duration: Total song duration
            metadata_ready: Whether metadata is ready for lyrics fetch

        Returns:
            Formatted lyrics section as a string
        """
        try:
            # Skip if lyrics handler is not available
            if not self.lyrics_handler.has_lyrics_support():
                return "\n\n[bold magenta]─── Lyrics ───[/bold magenta]\n[italic yellow]Lyrics feature not available[/italic yellow]"

            # Enhanced logging to debug lyrics problems
            logger.debug(
                f"Processing lyrics for '{song}' (metadata ready: {metadata_ready})"
            )

            # Check cache for lyrics
            cached_lyrics = self.lyrics_handler.get_from_cache(song, artist, album)

            if cached_lyrics:
                logger.debug(
                    f"Found cached lyrics for '{song}' ({len(cached_lyrics)} lines)"
                )
            else:
                logger.debug(f"No cached lyrics found for '{song}'")

            # If lyrics not in cache and metadata is ready, fetch them
            if not cached_lyrics and metadata_ready:
                try:
                    logger.info(f"Fetching lyrics for '{song}'")
                    lyrics_lines = self.lyrics_handler.fetch_lyrics(
                        song, artist, album, duration
                    )
                    if lyrics_lines:
                        logger.info(
                            f"Successfully fetched lyrics for '{song}' ({len(lyrics_lines)} lines)"
                        )
                        self.lyrics_handler.store_in_cache(
                            lyrics_lines, song, artist, album
                        )
                        cached_lyrics = lyrics_lines
                    else:
                        logger.info(f"No lyrics found for '{song}'")
                except LyricsError as e:
                    logger.error(f"Error fetching lyrics: {e}")
                    return f"\n\n[bold magenta]─── Lyrics ───[/bold magenta]\n[italic red]Error: {str(e)}[/italic red]"

            # If we have lyrics, display them
            if cached_lyrics:
                lyrics_content = self.lyrics_handler.create_focused_lyrics_view(
                    cached_lyrics, elapsed, song, artist, album
                )
                return (
                    f"\n\n[bold magenta]─── Lyrics ───[/bold magenta]\n{lyrics_content}"
                )

            # If metadata is not ready, show waiting message
            if not metadata_ready:
                return "\n\n[bold magenta]─── Lyrics ───[/bold magenta]\n[italic yellow]Waiting for song metadata...[/italic yellow]"

            # No lyrics available
            return "\n\n[bold magenta]─── Lyrics ───[/bold magenta]\n[italic yellow]No lyrics available for this song[/italic yellow]"

        except Exception as e:
            logger.error(f"Error processing lyrics for display: {e}")
            return f"\n\n[bold magenta]─── Lyrics ───[/bold magenta]\n[italic red]Error processing lyrics: {str(e)}[/italic red]"

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
        Create the content for the display panel.

        Args:
            song: Current song name
            artist: Artist name
            album: Album name
            elapsed: Current playback position
            duration: Total duration
            lyrics_section: Formatted lyrics section

        Returns:
            Rich Group object containing display content
        """
        # Get song source indicator (history or searched)
        song_source = self._get_song_source()

        # Format song info
        info_text = self._format_song_info(song, artist, album, song_source)

        # Create progress bar
        progress = self._create_progress_bar(elapsed, duration)

        # Get status text
        status_text = self._get_status_text()

        # Add user feedback if available
        user_feedback = self._get_user_feedback_text()

        # Create the content group - FIXED: Simplified the lyrics display logic
        if self._show_lyrics:
            # Always include lyrics section if show_lyrics is True, even if empty
            # This ensures we at least show "waiting for lyrics" message
            if user_feedback:
                content = Group(
                    info_text, progress, status_text, user_feedback, lyrics_section
                )
            else:
                content = Group(info_text, progress, status_text, lyrics_section)
        else:
            if user_feedback:
                content = Group(info_text, progress, status_text, user_feedback)
            else:
                content = Group(info_text, progress, status_text)

        return content

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

    def _create_display_panel(self, content: Group, controls_text: str) -> Panel:
        """
        Create the main display panel.

        Args:
            content: The content group to display
            controls_text: Text describing keyboard controls

        Returns:
            Rich Panel object
        """
        return Panel(
            content,
            title="♫ Aurras Music Player ♫",
            border_style="cyan",
            box=HEAVY,
            padding=(0, 1),
            subtitle=controls_text,
            subtitle_align="right",
        )

    # --- Utility Methods ---

    @staticmethod
    def _normalize_str(s: Optional[str]) -> str:
        """
        Normalize a string for more reliable cache lookups.

        Args:
            s: The string to normalize

        Returns:
            Normalized string (lowercase, trimmed, or empty string if None/Unknown)
        """
        if not s or s == "Unknown":
            return ""
        return s.lower().strip()

    def _generate_lyrics_cache_keys(
        self, song: str, artist: str, album: str
    ) -> Tuple[str, str]:
        """
        Generate cache keys for lyrics lookup.

        Args:
            song: Song name
            artist: Artist name
            album: Album name

        Returns:
            Tuple of (full_key, song_only_key)
        """
        # Create a full key with all metadata
        full_key = f"{self._normalize_str(song)}_{self._normalize_str(artist)}_{self._normalize_str(album)}"

        # Create a fallback key with just the song name
        song_only_key = self._normalize_str(song)

        return full_key, song_only_key

    def _get_lyrics_from_cache(
        self, song: str, artist: str, album: str
    ) -> Optional[List[str]]:
        """
        Retrieve lyrics from cache if available.

        Args:
            song: Song name
            artist: Artist name
            album: Album name

        Returns:
            Cached lyrics if found, None otherwise
        """
        full_key, song_only_key = self._generate_lyrics_cache_keys(song, artist, album)

        # Try full key first (most specific match)
        if full_key in self._lyrics_cache:
            logger.debug(f"Using memory-cached lyrics for '{song}' (full key match)")
            return self._lyrics_cache[full_key]

        # Fall back to song-only key
        if song_only_key in self._lyrics_cache:
            logger.debug(
                f"Using memory-cached lyrics for '{song}' (song-only key match)"
            )
            return self._lyrics_cache[song_only_key]

        # Not found in cache
        return None

    def _cache_lyrics(
        self, lyrics: List[str], song: str, artist: str, album: str
    ) -> None:
        """
        Store lyrics in cache with appropriate keys.

        Args:
            lyrics: The lyrics to cache
            song: Song name
            artist: Artist name
            album: Album name
        """
        full_key, song_only_key = self._generate_lyrics_cache_keys(song, artist, album)

        # Store with both keys for better future matching
        self._lyrics_cache[full_key] = lyrics
        self._lyrics_cache[song_only_key] = lyrics

        logger.debug(f"Cached lyrics for '{song}' with {len(lyrics)} lines")

    def _create_focused_lyrics_view(
        self, lyrics_lines: List[str], current_time: float, context_lines: int = 3
    ) -> str:
        """
        Create a focused view of lyrics with the current line highlighted and only a few surrounding lines.

        Args:
            lyrics_lines: List of lyrics lines with timestamps
            current_time: Current playback position in seconds
            context_lines: Number of lines to show above and below current line

        Returns:
            Formatted lyrics text with highlighting
        """
        if not lyrics_lines:
            return "[italic]No lyrics available[/italic]"

        # Parse timestamps and build a list of (timestamp, text) tuples
        parsed_lyrics = []
        timestamp_pattern = r"\[(\d+):(\d+\.\d+)\](.*?)(?=\[\d+:\d+\.\d+\]|$)"

        # First, collect all timestamp-text pairs from all lines
        for line in lyrics_lines:
            matches = re.finditer(timestamp_pattern, line)
            for match in matches:
                minutes = int(match.group(1))
                seconds = float(match.group(2))
                timestamp = minutes * 60 + seconds
                text = match.group(3).strip()
                if text:  # Only add if there's actual text
                    parsed_lyrics.append((timestamp, text))

        # Sort by timestamp in case they're not in order
        parsed_lyrics.sort(key=lambda x: x[0])

        if not parsed_lyrics:
            return "[italic]Could not parse lyrics timestamps[/italic]"

        # Find the current line based on timestamp
        current_index = 0
        for i, (timestamp, _) in enumerate(parsed_lyrics):
            if timestamp > current_time:
                break
            current_index = i

        # Calculate the range of lines to display
        start_index = max(0, current_index - context_lines)
        end_index = min(len(parsed_lyrics), current_index + context_lines + 1)

        # Build the focused lyrics display with highlighting
        result_lines = []

        # Add a header showing current position if we're not at the beginning
        if start_index > 0:
            result_lines.append("[dim]...[/dim]")

        # Add the lines with appropriate highlighting, but without timestamps
        for i in range(start_index, end_index):
            _, text = parsed_lyrics[i]

            if i == current_index:
                # Current line - highlight with bold green (no timestamp shown)
                result_lines.append(f"[bold green]{text}[/bold green]")
            else:
                # Other lines - dim text for better contrast (no timestamp shown)
                result_lines.append(f"[dim]{text}[/dim]")

        # Add a footer if we're not at the end
        if end_index < len(parsed_lyrics):
            result_lines.append("[dim]...[/dim]")

        return "\n".join(result_lines)

    def _get_current_song_name(self) -> str:
        """Get the name of the currently playing song."""
        if 0 <= self._current_playlist_pos < len(self._current_song_names):
            return self._current_song_names[self._current_playlist_pos]
        return "Unknown"

    def _get_song_source(self) -> str:
        """Get the source indicator for the current song (history or searched)."""
        if (
            self._history_song_count > 0
            and self._current_playlist_pos < self._queue_start_index
        ):
            return " [dim](From History)[/dim]"
        return ""

    def _format_song_info(
        self, song_name: str, artist: str, album: str, source: str
    ) -> str:
        """
        Format song information for display.

        Args:
            song_name: Name of the song
            artist: Artist name
            album: Album name
            source: Source indicator (e.g., "From History")

        Returns:
            Formatted song information text
        """
        # Start with the song name
        info_text = f"[bold green]Now Playing:[/] [bold yellow]{song_name}[/]{source}"
        # Add artist if available
        if artist != "Unknown" and artist.strip():
            info_text += f"\n[bold magenta]Artist:[/] [yellow]{artist}[/]"

        # Add album if available
        if album != "Unknown" and album.strip():
            info_text += f" [dim]·[/] [bold magenta]Album:[/] [yellow]{album}[/]"

        # Add position information
        position_info = f"[dim]Song {self._current_playlist_pos + 1} of {len(self._current_song_names)}[/dim]"
        info_text += f"\n{position_info}"

        return info_text

    def _create_progress_bar(self, elapsed: float, duration: float) -> Progress:
        """
        Create a progress bar for song playback.

        Args:
            elapsed: Current playback position in seconds
            duration: Total song duration in seconds

        Returns:
            Rich Progress object configured for song playback
        """
        progress = Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40, style="cyan", complete_style="green"),
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

    def _get_status_text(self) -> str:
        """Get the current player status text."""
        try:
            status = "Paused" if self.pause else "Playing"
            vol = self.volume
            return f"[dim]Status: {status} · Volume: {vol}%[/]"
        except ShutdownError:
            self._stop_requested = True
            return "[dim]Status: Stopped[/]"
        except Exception:
            return "[dim]Status: Unknown[/]"

    def _format_time(self, seconds: float) -> str:
        """
        Format time in seconds to MM:SS format.

        Args:
            seconds: Time in seconds

        Returns:
            Formatted time string
        """
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
