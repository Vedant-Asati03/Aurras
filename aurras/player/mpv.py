"""MPV player with enhanced UI and functionality."""

import time
import locale
import logging
import threading
from typing import Dict, Any, List, Optional

from rich.console import Console, Group
from rich.panel import Panel
from rich.live import Live
from rich.progress import TextColumn, BarColumn, Progress
from rich.box import ROUNDED

from . import python_mpv as mpv
from .python_mpv import ShutdownError

try:
    from ..services.lyrics import LyricsManager, LYRICS_AVAILABLE
except ImportError:
    LYRICS_AVAILABLE = False
    LyricsManager = None  # Add proper fallback for LyricsManager

# Set up logging
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
        # Initialize lyrics manager only if available
        self.lyrics_manager = (
            LyricsManager() if LYRICS_AVAILABLE and LyricsManager else None
        )
        self._lyrics_cache = {}  # Initialize lyrics cache
        self._reset_metadata_ready_flag = False  # Initialize reset flag
        self._is_playing = False
        self._stop_requested = False
        self._display_thread: Optional[threading.Thread] = None
        self._progress_thread: Optional[threading.Thread] = None
        self._progress_instance = None
        self._elapsed_time: float = 0
        self._current_playlist_pos: int = 0
        self._current_song_names: List[str] = []
        self._history_song_count: int = (
            0  # Track how many history songs are in the queue
        )
        self._queue_start_index: int = 0  # Index where searched songs start

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
            self.console.print("[yellow]Quit key pressed[/yellow]")
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
            self.playlist_prev()

        @self.on_key_press("n")
        def _play_next() -> None:
            logger.debug("Next key pressed")
            self.playlist_next()

    # --- Event handlers ---

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
            # This will force the display to wait for new metadata before fetching lyrics
            self._reset_metadata_ready_flag = True

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
        logger.debug(f"Volume increased to {new_volume}")

    def _handle_volume_down_event(self) -> None:
        """Handle down arrow key event to decrease volume."""
        new_volume = max(0, self.volume - 5)
        self.set_volume(new_volume)
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
            song_name: Name of the song to display initially
        """
        try:
            # Define control key information
            controls_text = (
                "[white][bold cyan]Space[/]:Pause · "
                "[bold cyan]q[/]:Quit · "
                "[bold cyan]b[/]:Prev · "
                "[bold cyan]n[/]:Next · "
                "[bold cyan]←→[/]:Seek · "
                "[bold cyan]↑↓[/]:Volume[/]"
            )

            # Track the last displayed song to avoid unnecessary lyrics fetching
            last_displayed_song = None
            last_playlist_pos = -1
            cached_lyrics = []  # Start with empty lyrics
            lyrics_fetched = False
            metadata_ready = False
            metadata_checked = False
            lyrics_retry_count = 0
            max_lyrics_retries = 5
            refresh_count = 0
            show_lyrics_panel = False  # Flag to control lyrics panel visibility

            # Reset metadata flag
            self._reset_metadata_ready_flag = False

            # Wait a short moment before initial display to allow metadata to load
            time.sleep(0.5)

            # Create a live display that updates automatically
            with Live(
                refresh_per_second=4,  # Lower refresh rate for efficiency
                console=self.console,
                transient=True,
            ) as live:
                while not self._stop_requested and self._is_playing:
                    try:
                        # Get current playback position
                        elapsed = self._elapsed_time or 0
                        duration = self.duration or 0

                        # Check if playlist position changed
                        playlist_position_changed = (
                            last_playlist_pos != self._current_playlist_pos
                        )
                        if playlist_position_changed:
                            logger.debug(
                                f"Display detected playlist position change: {last_playlist_pos} -> {self._current_playlist_pos}"
                            )
                            last_playlist_pos = self._current_playlist_pos

                            # Reset counters when changing songs
                            refresh_count = 0
                            lyrics_retry_count = 0
                            lyrics_fetched = False
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
                                if (
                                    duration > 0
                                    and artist != "Unknown"
                                    and album != "Unknown"
                                ):
                                    metadata_ready = True
                                    logger.debug(
                                        "Metadata is ready for lyrics fetching"
                                    )
                                else:
                                    logger.debug(
                                        "Metadata not yet complete for lyrics fetching"
                                    )

                            # Check metadata periodically to see if it's been updated
                            if refresh_count % 5 == 0 and not metadata_ready:
                                if (
                                    duration > 0
                                    and artist != "Unknown"
                                    and album != "Unknown"
                                ):
                                    metadata_ready = True
                                    logger.debug(
                                        "Metadata is now ready for lyrics fetching"
                                    )
                                # If no metadata after 15 refreshes, try fetching with what we have
                                elif refresh_count > 15:
                                    logger.debug(
                                        "Attempting lyrics fetch with incomplete metadata"
                                    )
                                    metadata_ready = True
                        except Exception:
                            artist = "Unknown"
                            album = "Unknown"

                        # Calculate progress percentage
                        try:
                            progress_percent = (
                                (elapsed / duration) * 100 if duration > 0 else 0
                            )
                        except ShutdownError:
                            self._stop_requested = True
                            break
                        except ZeroDivisionError:
                            progress_percent = 0

                        # Get current song name and source (history or searched)
                        current_song = self._get_current_song_name()
                        song_source = self._get_song_source()

                        # Create song information text
                        info_text = self._format_song_info(
                            current_song, artist, album, song_source
                        )

                        # Create progress bar
                        progress = self._create_progress_bar(elapsed, duration)

                        # Create content group for the panel
                        content = Group(
                            info_text,
                            progress,
                            self._get_status_text(),
                            controls_text,
                        )

                        panel = Panel(
                            content,
                            title="♫ Aurras Music Player ♫",
                            border_style="cyan",
                            box=ROUNDED,
                            padding=(0, 1),
                        )

                        # Handle lyrics update
                        try:
                            # Skip lyrics handling if lyrics manager is not available
                            if not self.lyrics_manager or not LYRICS_AVAILABLE:
                                # Don't set show_lyrics_panel if lyrics aren't available
                                lyrics_fetched = True
                            else:
                                # Determine if we need to fetch/update lyrics
                                lyrics_need_update = False

                                # Song changed - need to fetch new lyrics
                                if current_song != last_displayed_song:
                                    lyrics_need_update = True
                                    lyrics_fetched = False
                                    lyrics_retry_count = 0
                                    cached_lyrics = []  # Reset to empty
                                    show_lyrics_panel = (
                                        False  # Hide lyrics panel on song change
                                    )
                                    last_displayed_song = current_song
                                    logger.debug(f"Song changed to: {current_song}")

                                # Retry if we have metadata now but didn't before
                                if (
                                    not lyrics_fetched
                                    and metadata_ready
                                    and lyrics_retry_count < max_lyrics_retries
                                ):
                                    lyrics_need_update = True

                                # Normalize string for more reliable cache lookup
                                def normalize_str(s):
                                    if not s or s == "Unknown":
                                        return ""
                                    return s.lower().strip()

                                # Create more reliable cache keys
                                simple_key = f"{normalize_str(current_song)}_{normalize_str(artist)}_{normalize_str(album)}"

                                # Also try a song-only key as fallback
                                song_only_key = normalize_str(current_song)

                                # Check memory cache first before fetching
                                if simple_key in self._lyrics_cache:
                                    cached_lyrics = self._lyrics_cache[simple_key]
                                    lyrics_fetched = True
                                    lyrics_need_update = False
                                    show_lyrics_panel = bool(
                                        cached_lyrics
                                    )  # Show panel if we have lyrics
                                    logger.debug(
                                        f"Using memory-cached lyrics for '{current_song}' (full key)"
                                    )
                                elif song_only_key in self._lyrics_cache:
                                    cached_lyrics = self._lyrics_cache[song_only_key]
                                    lyrics_fetched = True
                                    lyrics_need_update = False
                                    show_lyrics_panel = bool(
                                        cached_lyrics
                                    )  # Show panel if we have lyrics
                                    logger.debug(
                                        f"Using memory-cached lyrics for '{current_song}' (song-only key)"
                                    )

                                # Try to fetch lyrics if needed and we have good metadata
                                if lyrics_need_update and metadata_ready:
                                    try:
                                        logger.debug(
                                            f"Attempting to fetch lyrics for '{current_song}' (try {lyrics_retry_count + 1}/{max_lyrics_retries})"
                                        )
                                        new_lyrics = self._display_lyrics(
                                            current_song, artist, album, duration
                                        )

                                        # Make sure we always have a list of strings
                                        if isinstance(new_lyrics, str):
                                            new_lyrics = new_lyrics.split("\n")

                                        # Make sure the list has items
                                        if not new_lyrics:
                                            new_lyrics = [
                                                f"[italic yellow]No lyrics found for:[/italic yellow] [bold]{current_song}[/bold]"
                                            ]

                                        # Log what we received for debugging
                                        logger.debug(
                                            f"Received lyrics for '{current_song}': {len(new_lyrics)} lines, first line: '{new_lyrics[0][:50]}...'"
                                        )

                                        # Check if we got real lyrics - less strict check for cached content
                                        has_error_message = any(
                                            (
                                                "Error" in line
                                                or "error" in line
                                                or "Not available" in line
                                                or "not available" in line
                                            )
                                            for line in new_lyrics[:3]
                                        )

                                        if new_lyrics and not has_error_message:
                                            # We got meaningful lyrics
                                            cached_lyrics = new_lyrics
                                            lyrics_fetched = True
                                            show_lyrics_panel = (
                                                True  # Show panel with fetched lyrics
                                            )
                                            # Store in memory cache (both keys for better future matching)
                                            self._lyrics_cache[simple_key] = new_lyrics
                                            self._lyrics_cache[song_only_key] = (
                                                new_lyrics
                                            )
                                            logger.info(
                                                f"Successfully fetched lyrics for '{current_song}'"
                                            )
                                        elif any(
                                            ("No lyrics found" in line)
                                            for line in new_lyrics
                                        ):
                                            # Lyrics service confirmed no lyrics exist
                                            cached_lyrics = new_lyrics
                                            lyrics_fetched = True
                                            show_lyrics_panel = (
                                                True  # Show "no lyrics found" message
                                            )
                                            # Cache negative results too
                                            self._lyrics_cache[simple_key] = new_lyrics
                                            self._lyrics_cache[song_only_key] = (
                                                new_lyrics
                                            )
                                            logger.info(
                                                f"No lyrics available for '{current_song}'"
                                            )
                                        else:
                                            # Got empty or minimal response, might need retry
                                            lyrics_retry_count += 1
                                            if lyrics_retry_count >= max_lyrics_retries:
                                                cached_lyrics = [
                                                    f"[italic yellow]Could not find lyrics after {max_lyrics_retries} attempts[/italic yellow]"
                                                ]
                                                lyrics_fetched = True
                                                show_lyrics_panel = True  # Show error message after max retries
                                                # Cache negative results after max retries
                                                self._lyrics_cache[simple_key] = (
                                                    cached_lyrics
                                                )
                                                self._lyrics_cache[song_only_key] = (
                                                    cached_lyrics
                                                )
                                                logger.warning(
                                                    f"Failed to find lyrics for '{current_song}' after {max_lyrics_retries} attempts"
                                                )
                                    except Exception as e:
                                        lyrics_retry_count += 1
                                        logger.error(
                                            f"Error fetching lyrics for '{current_song}' (attempt {lyrics_retry_count}): {e}"
                                        )
                                        if lyrics_retry_count >= max_lyrics_retries:
                                            cached_lyrics = [
                                                f"[italic red]Error fetching lyrics:[/italic red] {str(e)}"
                                            ]
                                            lyrics_fetched = True
                                            show_lyrics_panel = True  # Show error message after max retries
                                            # Cache error messages too to avoid repeated failures
                                            self._lyrics_cache[simple_key] = (
                                                cached_lyrics
                                            )

                            # Don't update with waiting message - we'll just not show the panel
                        except Exception as e:
                            logger.error(f"Error in lyrics handling: {e}")
                            if (
                                lyrics_fetched
                            ):  # Only show error if we were displaying lyrics already
                                cached_lyrics = [
                                    "[italic red]Error processing lyrics[/italic red]"
                                ]
                                show_lyrics_panel = True

                        # Create the main player panel
                        panel = Panel(
                            content,
                            title="♫ Aurras Music Player ♫",
                            border_style="cyan",
                            box=ROUNDED,
                            padding=(0, 1),
                        )

                        # Create display group - conditionally include lyrics panel
                        if show_lyrics_panel and cached_lyrics:
                            # Process lyrics content only if we're showing the panel
                            try:
                                # Make sure cached_lyrics is a list
                                if not isinstance(cached_lyrics, list):
                                    cached_lyrics = (
                                        str(cached_lyrics).split("\n")
                                        if cached_lyrics
                                        else []
                                    )

                                # Join the list into a string
                                lyrics_content = "\n".join(cached_lyrics)

                                # Ensure content is not empty
                                if not lyrics_content.strip():
                                    lyrics_content = "[italic]No lyrics available for this song[/italic]"
                            except Exception as e:
                                logger.error(f"Error formatting lyrics: {e}")
                                lyrics_content = (
                                    "[italic red]Error formatting lyrics[/italic red]"
                                )

                            # Create lyrics panel
                            lyrics_panel = Panel(
                                lyrics_content,
                                title="Lyrics",
                                border_style="magenta",
                                box=ROUNDED,
                                padding=(0, 1),
                            )

                            # Include both panels in the display
                            display_group = Group(panel, lyrics_panel)
                        else:
                            # Only include the main player panel
                            display_group = panel

                        # Update the display
                        live.update(display_group)

                        time.sleep(0.25)

                    except ShutdownError:
                        # Handle mpv shutdown gracefully
                        self._stop_requested = True
                        logger.debug("MPV shutdown during display update")
                        break
                    except Exception as e:
                        # Log display errors but continue
                        self.console.print(
                            f"[bold red]Display update error: {str(e)}[/]"
                        )
                        logger.error(f"Display update error: {e}")
                        time.sleep(0.5)
        except Exception as e:
            logger.error(f"Display thread error: {e}")
            self.console.print(f"[bold red]Display error: {str(e)}[/]")

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

    def _display_lyrics(
        self, song_name: str, artist_name: str, album_name: str, duration: float
    ) -> List[str]:
        """
        Fetch lyrics for the current song.

        Args:
            song_name: Name of the song to fetch lyrics for
            artist_name: Artist name
            album_name: Album name
            duration: Song duration in seconds

        Returns:
            List of lyrics lines or empty list if no lyrics found
        """
        # Return early if lyrics manager is not available
        if not self.lyrics_manager or not LYRICS_AVAILABLE:
            return ["[italic yellow]Lyrics feature not available[/italic yellow]"]

        # Check if we have valid inputs
        if not song_name or song_name == "Unknown":
            return ["[italic yellow]Waiting for song information...[/italic yellow]"]

        # Validate metadata is not default values
        valid_metadata = True
        if artist_name == "Unknown" or not artist_name.strip():
            logger.debug("Artist name not available for lyrics fetch")
            valid_metadata = False

        if album_name == "Unknown" or not album_name.strip():
            logger.debug("Album name not available for lyrics fetch")
            valid_metadata = False

        if duration <= 0:
            logger.debug("Duration not available for lyrics fetch")
            valid_metadata = False

        if not valid_metadata:
            return [
                "[italic yellow]Waiting for complete song metadata...[/italic yellow]"
            ]

        # We should use integers for duration when obtaining lyrics
        duration_int = int(duration) if duration else 0

        logger.debug(
            f"Fetching lyrics for: '{song_name}' by '{artist_name}' from album '{album_name}' (duration: {duration_int}s)"
        )

        try:
            # The LyricsManager.obtain_lyrics_info method will check the database cache first
            lyrics_info = self.lyrics_manager.obtain_lyrics_info(
                song_name, artist_name, album_name, duration_int
            )

            if not lyrics_info:
                logger.info(f"No lyrics info returned for: {song_name}")
                return [
                    f"[italic yellow]No lyrics found for:[/italic yellow] [bold]{song_name}[/bold]"
                ]

            # Add detailed logging of what we received
            logger.debug(f"Lyrics info keys received: {', '.join(lyrics_info.keys())}")

            if "synced_lyrics" in lyrics_info and lyrics_info["synced_lyrics"]:
                # Handle different formats that might be returned
                synced_lyrics = lyrics_info["synced_lyrics"]

                # Convert to list if we got a string
                if isinstance(synced_lyrics, str):
                    # Split string into lines
                    lyrics_list = synced_lyrics.split("\n")
                    logger.debug(
                        f"Converted synced lyrics string to list of {len(lyrics_list)} lines"
                    )
                elif isinstance(synced_lyrics, list):
                    # Already a list
                    lyrics_list = synced_lyrics
                    logger.debug(
                        f"Received synced lyrics as list with {len(lyrics_list)} lines"
                    )
                else:
                    # Convert anything else to string and split
                    lyrics_list = str(synced_lyrics).split("\n")
                    logger.debug(
                        f"Converted synced lyrics of type {type(synced_lyrics)} to list"
                    )

                # Make sure we have at least one line
                if not lyrics_list:
                    lyrics_list = [
                        f"[italic yellow]Empty lyrics for:[/italic yellow] [bold]{song_name}[/bold]"
                    ]
                    logger.debug("Lyrics list was empty, using placeholder")

                logger.info(f"Found lyrics for: {song_name} ({len(lyrics_list)} lines)")
                return lyrics_list
            else:
                # Check for non-synced lyrics as fallback
                if "plain_lyrics" in lyrics_info and lyrics_info["plain_lyrics"]:
                    lyrics_text = lyrics_info["plain_lyrics"]
                    if isinstance(lyrics_text, str):
                        lyrics_list = lyrics_text.split("\n")
                    else:
                        lyrics_list = str(lyrics_text).split("\n")

                    logger.info(f"Found non-synced lyrics for: {song_name}")
                    return lyrics_list
                else:
                    logger.info(f"No lyrics found for: {song_name}")
                    return [
                        f"[italic yellow]No lyrics found for:[/italic yellow] [bold]{song_name}[/bold]"
                    ]
        except Exception as e:
            logger.error(f"Error fetching lyrics: {e}")
            return [f"[italic red]Error fetching lyrics:[/italic red] {str(e)}"]

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
