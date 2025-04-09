"""
MPV Player Module

This module provides an enhanced MPV player with rich UI, lyrics integration,
and proper integration with the unified database structure.
"""

import time
import locale
import logging
import gc
from enum import Enum, auto
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, Future
from rich.box import HEAVY
from rich.live import Live
from rich.panel import Panel
from rich.console import Group
from rich.progress import TextColumn, BarColumn, Progress
import weakref
from functools import partial
from collections import deque

from ..core.settings import KeyboardShortcuts, Settings
from ..player.history import RecentlyPlayedManager
from ..utils.exceptions import DisplayError
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
from . import python_mpv as mpv
from .python_mpv import ShutdownError
from .lyrics_handler import LyricsHandler
from .cache import LRUCache
from .memory import memory_stats_decorator, optimize_memory_usage

logger = logging.getLogger(__name__)

# Type aliases for better readability
ThemeDict = Dict[str, Any]
SongInfo = Tuple[str, str, str]  # song, artist, album
PLAYERSETTINGS = Settings()
KEYBOARDSHORTCUTS = KeyboardShortcuts()


class PlaybackState(Enum):
    """Enum for player playback states."""

    PLAYING = auto()
    PAUSED = auto()
    STOPPED = auto()


class FeedbackType(Enum):
    """Enum for user feedback categories."""

    PLAYBACK = auto()  # Play/pause/stop actions
    NAVIGATION = auto()  # Next/previous/jump tracks
    VOLUME = auto()  # Volume changes
    SEEKING = auto()  # Forward/backward seeking
    THEME = auto()  # Theme changes
    LYRICS = auto()  # Lyrics toggle
    SYSTEM = auto()  # System messages
    ERROR = auto()  # Error messages


class LyricsStatus(Enum):
    """Enum for lyrics availability states."""

    LOADING = auto()  # Lyrics are being fetched
    AVAILABLE = auto()  # Lyrics are available and loaded
    NOT_FOUND = auto()  # No lyrics found for the song
    DISABLED = auto()  # Lyrics feature is disabled


class HistoryCategory(Enum):
    """Enum for categorizing songs based on play count."""

    NEW = 1  # First play
    OCCASIONAL = 2  # Played 2-5 times
    REGULAR = 3  # Played 6-10 times
    FAVORITE = 4  # Played more than 10 times


@dataclass
class Metadata:
    """Data class for song metadata."""

    title: str = "Unknown"
    artist: str = "Unknown"
    album: str = "Unknown"
    duration: float = 0


@dataclass
class PlayerState:
    """Data class for player state information."""

    show_lyrics: bool = True
    playback_state: PlaybackState = PlaybackState.STOPPED
    stop_requested: bool = False
    elapsed_time: float = 0
    current_refresh_rate: float = 0.25
    current_theme: Optional[str] = None
    metadata_ready: bool = False
    current_playlist_pos: int = 0
    queue_start_index: int = 0
    jump_mode: bool = False
    jump_number: str = ""


@dataclass
class UserFeedback:
    """Data class for user action feedback."""

    action: str
    description: str
    feedback_type: FeedbackType
    timestamp: float
    timeout: float = 1.5


@dataclass
class HistoryData:
    """Data class for song history information."""

    play_count: int = 1
    category: HistoryCategory = HistoryCategory.NEW
    last_played: Optional[int] = None
    loaded: bool = False


@dataclass
class LyricsState:
    """Data class for lyrics state."""

    status: LyricsStatus = LyricsStatus.LOADING
    future: Optional[Future] = None
    cached_lyrics: Optional[List[str]] = None
    no_lyrics_message: Optional[str] = None


class WeakPropertyObserver:
    """
    Weak reference-based property observer to prevent memory leaks.

    This class creates property observers that don't hold strong references
    to their parent objects, preventing memory leaks through circular references.
    """

    def __init__(self, instance, property_name, callback):
        """
        Create a weak reference observer.

        Args:
            instance: The MPV player instance
            property_name: Name of the property to observe
            callback: Callback function to call when property changes
        """
        self.instance_ref = weakref.ref(instance)
        self.property_name = property_name
        self.callback = callback
        self.registered = False

    def register(self):
        """Register the observer with the MPV instance."""
        instance = self.instance_ref()
        if instance is not None:
            instance.observe_property(self.property_name, self.callback)
            self.registered = True

    def unregister(self):
        """Unregister the observer from the MPV instance."""
        instance = self.instance_ref()
        if instance is not None and self.registered:
            try:
                instance.unobserve_property(self.property_name, self.callback)
                self.registered = False
            except Exception as e:
                logger.debug(f"Error unregistering observer: {e}")

    def __del__(self):
        """Automatically unregister when garbage collected."""
        self.unregister()


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
        self._setup_weak_property_observers()
        self._setup_key_bindings()

        # Track active futures for proper cleanup
        self._active_futures = set()

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

    # ? --- Property Observers ---

    def _setup_weak_property_observers(self) -> None:
        """Set up property observers using weak references to prevent memory leaks."""
        # Store observers in a list so they aren't garbage collected
        self._observers = []

        # Create observer for pause changes
        pause_observer = WeakPropertyObserver(self, "pause", self._on_pause_change)
        pause_observer.register()
        self._observers.append(pause_observer)

        # Create observer for duration changes
        duration_observer = WeakPropertyObserver(
            self, "duration", self._on_duration_change
        )
        duration_observer.register()
        self._observers.append(duration_observer)

        # Create observer for metadata changes
        metadata_observer = WeakPropertyObserver(
            self, "metadata", self._on_metadata_change
        )
        metadata_observer.register()
        self._observers.append(metadata_observer)

        # Create observer for playlist position changes
        playlist_observer = WeakPropertyObserver(
            self, "playlist-pos", self._on_playlist_pos_change
        )
        playlist_observer.register()
        self._observers.append(playlist_observer)

        # Create observer for time position with direct property observer
        @self.property_observer("time-pos")
        def _track_time_pos(_name: str, value: Optional[float]) -> None:
            # This is safe because it's a primitive type (float)
            # and doesn't create circular references
            if hasattr(self, "_state"):
                self._state.elapsed_time = value if value is not None else 0

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

    # & --- Key Bindings ---

    def _setup_key_bindings(self) -> None:
        """Set up keyboard controls for the player."""

        # Quit handler
        @self.on_key_press(KEYBOARDSHORTCUTS.quit_playback)
        def _quit() -> None:
            self._show_user_feedback("Quit", "Exiting player", FeedbackType.SYSTEM)
            self._state.stop_requested = True
            self._state.playback_state = PlaybackState.STOPPED
            self.quit()

        # Volume control
        @self.on_key_press(KEYBOARDSHORTCUTS.volume_up)
        def _volume_up() -> None:
            new_volume = min(130, self.volume + 5)
            self.volume = new_volume
            self._show_user_feedback(
                "Volume", f"Increased to {new_volume}%", FeedbackType.VOLUME
            )

        @self.on_key_press(KEYBOARDSHORTCUTS.volume_down)
        def _volume_down() -> None:
            new_volume = max(0, self.volume - 5)
            self.volume = new_volume
            self._show_user_feedback(
                "Volume", f"Decreased to {new_volume}%", FeedbackType.VOLUME
            )

        # Toggle lyrics display
        @self.on_key_press(KEYBOARDSHORTCUTS.toggle_lyrics)
        def _toggle_lyrics() -> None:
            self._state.show_lyrics = not self._state.show_lyrics
            action = "Showing" if self._state.show_lyrics else "Hiding"

            # Update lyrics status based on visibility
            if not self._state.show_lyrics:
                self._lyrics.status = LyricsStatus.DISABLED
            elif self._lyrics.cached_lyrics:
                self._lyrics.status = LyricsStatus.AVAILABLE
            else:
                self._lyrics.status = LyricsStatus.LOADING

            self._show_user_feedback(
                "Lyrics", f"{action} lyrics display", FeedbackType.LYRICS
            )

        # Seeking
        @self.on_key_press(KEYBOARDSHORTCUTS.seek_forward)
        def _seek_forward() -> None:
            self.seek(10)
            self._show_user_feedback("Seek", "Forward 10s", FeedbackType.SEEKING)

        @self.on_key_press(KEYBOARDSHORTCUTS.seek_backward)
        def _seek_backward() -> None:
            self.seek(-10)
            self._show_user_feedback("Seek", "Backward 10s", FeedbackType.SEEKING)

        # Jump mode for playlist navigation
        self._state.jump_mode = False
        self._state.jump_number = ""

        # Single handler for all number keys
        def _handle_number_key(key: str) -> None:
            self._state.jump_mode = True
            self._state.jump_number += key
            self._show_user_feedback(
                "Jump Mode",
                f"Jump {self._state.jump_number} tracks, press {KEYBOARDSHORTCUTS.previous_track}/{KEYBOARDSHORTCUTS.next_track}",
                FeedbackType.NAVIGATION,
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
        @self.on_key_press(KEYBOARDSHORTCUTS.next_track)
        def _next_track() -> None:
            if self._state.jump_mode:
                try:
                    jump_amount = (
                        int(self._state.jump_number) if self._state.jump_number else 1
                    )
                    self._execute_playlist_jump(jump_amount)
                    self._show_user_feedback(
                        "Jump", f"Forward {jump_amount} tracks", FeedbackType.NAVIGATION
                    )
                except ValueError:
                    self._show_user_feedback(
                        "Error", "Invalid jump number", FeedbackType.ERROR
                    )
                finally:
                    self._state.jump_mode = False
                    self._state.jump_number = ""
            else:
                self._show_user_feedback(
                    "Next", "Playing next track", FeedbackType.NAVIGATION
                )
                self.playlist_next()

        @self.on_key_press(KEYBOARDSHORTCUTS.previous_track)
        def _prev_track() -> None:
            if self._state.jump_mode:
                try:
                    jump_amount = (
                        int(self._state.jump_number) if self._state.jump_number else 1
                    )
                    self._execute_playlist_jump(-jump_amount)
                    self._show_user_feedback(
                        "Jump",
                        f"Backward {jump_amount} tracks",
                        FeedbackType.NAVIGATION,
                    )
                except ValueError:
                    self._show_user_feedback(
                        "Error", "Invalid jump number", FeedbackType.ERROR
                    )
                finally:
                    self._state.jump_mode = False
                    self._state.jump_number = ""
            else:
                self._show_user_feedback(
                    "Previous", "Playing previous track", FeedbackType.NAVIGATION
                )
                self.playlist_prev()

        # Add escape key to cancel jump mode
        @self.on_key_press(KEYBOARDSHORTCUTS.stop_jump_mode)
        def _cancel_jump_mode() -> None:
            if self._state.jump_mode:
                self._state.jump_mode = False
                self._state.jump_number = ""
                self._show_user_feedback(
                    "Jump Mode", "Cancelled", FeedbackType.NAVIGATION
                )

        # Theme cycling - updated to ensure theme name is properly tracked
        @self.on_key_press(KEYBOARDSHORTCUTS.switch_themes)
        def _cycle_theme() -> None:
            available_themes = get_available_themes()
            current_theme = get_current_theme()

            try:
                current_index = available_themes.index(current_theme)
                # Get the next theme (wrapping around)
                next_index = (current_index + 1) % len(available_themes)
                next_theme = available_themes[next_index]

                change_theme(next_theme)
                self._state.current_theme = next_theme

                # Force cache reset for any theme-dependent elements
                self._lyrics.cached_lyrics = None

                self._show_user_feedback(
                    "Theme", f"Changed to {next_theme}", FeedbackType.THEME
                )
            except ValueError:
                # If the current theme isn't found in the list, start with first theme
                next_theme = available_themes[0]
                change_theme(next_theme)
                self._state.current_theme = next_theme

                self._lyrics.cached_lyrics = None

                self._show_user_feedback(
                    "Theme", f"Changed to {next_theme}", FeedbackType.THEME
                )

    # * --- Main Player API ---

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
                logger.debug("MPV core shutdown detected during playback, exiting cleanly")
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
            controls_text = (
                "[white][bold cyan]󱁐[/] Pause · "
                "[bold cyan]q[/] Quit · "
                "[bold cyan]b[/] Prev · "
                "[bold cyan]n[/] Next · "
                "[bold cyan]←→[/] Seek · "
                "[bold cyan]↑↓[/] Volume · "
                "[bold cyan]l[/] Lyrics · "
                "[bold cyan]t[/] Theme[/]"
            )

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
            album: Song duration in seconds
        """
        # Skip if we already have cached lyrics for this song
        if self._lyrics.cached_lyrics:
            self._lyrics.status = LyricsStatus.AVAILABLE
            return

        # Cancel any existing future to avoid memory leaks
        if self._lyrics.future and not self._lyrics.future.done():
            self._lyrics.future.cancel()

        # Define the fetch function with weak references to avoid memory leaks
        def fetch_lyrics():
            try:
                # First check memory cache (fast)
                cached = self.lyrics_handler.get_from_cache(song, artist, album)
                if cached:
                    logger.debug(f"Found lyrics in cache for '{song}'")
                    self._lyrics.status = LyricsStatus.AVAILABLE
                    return cached

                # If not in cache, fetch from service
                lyrics = self.lyrics_handler.fetch_lyrics(song, artist, album, duration)
                if lyrics:
                    logger.info(f"Successfully fetched lyrics for '{song}'")
                    # Store in cache (limit size to prevent memory bloat)
                    self.lyrics_handler.store_in_cache(lyrics, song, artist, album)
                    self._lyrics.status = LyricsStatus.AVAILABLE
                    return lyrics
                else:
                    logger.info(f"No lyrics found for '{song}'")
                    self._lyrics.status = LyricsStatus.NOT_FOUND
                    return []
            except Exception as e:
                logger.error(f"Error fetching lyrics: {e}")
                self._lyrics.status = LyricsStatus.NOT_FOUND
                return []

        # Launch the async fetch and track the future for cleanup
        self._lyrics.future = self._thread_pool.submit(fetch_lyrics)
        # Track active futures for proper cleanup
        if hasattr(self, "_active_futures"):
            self._active_futures.add(self._lyrics.future)
            # Add done callback to remove future from tracking set
            self._lyrics.future.add_done_callback(
                lambda f: self._active_futures.discard(f)
                if hasattr(self, "_active_futures")
                else None
            )

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

        This method handles different lyrics states:
        1. Lyrics feature not available
        2. Waiting for metadata
        3. Showing cached lyrics
        4. Showing freshly fetched lyrics
        5. Showing no lyrics message
        """
        # Get theme-consistent header
        header = self._get_lyrics_header()

        # Check prerequisites
        if (
            self._lyrics.status == LyricsStatus.DISABLED
            or not self.lyrics_handler.has_lyrics_support()
        ):
            return f"{header}{self._format_feedback_message('Lyrics feature not available')}"

        if not metadata_ready:
            return f"{header}{self._format_feedback_message('Waiting for song metadata...')}"

        # Display logic for different scenarios
        if self._lyrics.status == LyricsStatus.AVAILABLE and self._lyrics.cached_lyrics:
            return f"{header}{self._format_cached_lyrics(song, artist, album, elapsed)}"

        if self._lyrics.future and self._lyrics.future.done():
            return f"{header}{self._handle_completed_lyrics_fetch(song, artist, album, elapsed)}"

        if (
            self._lyrics.status == LyricsStatus.LOADING
            and self._lyrics.future
            and not self._lyrics.future.done()
        ):
            return f"{header}{self.lyrics_handler.get_waiting_message()}"

        # No fetch in progress and no cached lyrics
        if (
            self._lyrics.status == LyricsStatus.NOT_FOUND
            and self._lyrics.no_lyrics_message is None
        ):
            self._lyrics.no_lyrics_message = self.lyrics_handler.get_no_lyrics_message()

        return f"{header}{self._lyrics.no_lyrics_message or 'No lyrics available'}"

    def _get_lyrics_header(self) -> str:
        """Get a theme-consistent lyrics section header."""
        theme_style = get_gradient_style()
        header_color = theme_style.get(
            "primary", theme_style.get("title", ["magenta"])[0]
        )
        return f"\n\n[bold {header_color}]─── Lyrics ───[/bold {header_color}]\n"

    def _format_feedback_message(self, message: str) -> str:
        """Format a feedback message with theme-consistent styling."""
        feedback_text = apply_gradient_to_text(message, "feedback")
        return f"[italic]{feedback_text}[/italic]"

    def _format_cached_lyrics(
        self, song: str, artist: str, album: str, elapsed: float
    ) -> str:
        """Format cached lyrics for display."""
        # Safety check
        if not self._lyrics.cached_lyrics:
            return self.lyrics_handler.get_no_lyrics_message()

        # Determine lyrics type and display accordingly
        is_synced = self.lyrics_handler._is_synced_lyrics(self._lyrics.cached_lyrics)
        # is_enhanced = self.lyrics_handler._is_enhanced_lrc(self._lyrics.cached_lyrics)

        if is_synced:
            return self.lyrics_handler.create_focused_lyrics_view(
                self._lyrics.cached_lyrics, elapsed, song, artist, album
            )
        else:
            # For plain lyrics, use the gradient effect
            plain_lyrics = self.lyrics_handler._get_plain_lyrics(
                self._lyrics.cached_lyrics
            )
            return self.lyrics_handler._create_simple_gradient_view(plain_lyrics[:15])

    def _handle_completed_lyrics_fetch(
        self, song: str, artist: str, album: str, elapsed: float
    ) -> str:
        """Handle completed lyrics fetch operation."""
        try:
            lyrics = self._lyrics.future.result()

            if lyrics:
                self._lyrics.cached_lyrics = lyrics
                self._lyrics.status = LyricsStatus.AVAILABLE
                return self._format_cached_lyrics(song, artist, album, elapsed)
            else:
                # Get a stable "no lyrics" message
                self._lyrics.status = LyricsStatus.NOT_FOUND
                if self._lyrics.no_lyrics_message is None:
                    self._lyrics.no_lyrics_message = (
                        self.lyrics_handler.get_no_lyrics_message()
                    )
                return self._lyrics.no_lyrics_message

        except Exception as e:
            logger.error(f"Error retrieving lyrics: {e}")
            self._lyrics.status = LyricsStatus.NOT_FOUND
            return self.lyrics_handler.get_error_message(str(e))

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
        if not self._history.loaded:
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
        if self._state.show_lyrics and lyrics_section:
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

    def _get_user_feedback_text(self) -> Optional[str]:
        """
        Get formatted user feedback text if available and not expired.

        Returns:
            Formatted feedback text or None if no feedback to show
        """
        if not self._user_feedback:
            return None

        # Check if feedback has expired
        elapsed = time.time() - self._user_feedback.timestamp
        if elapsed > self._user_feedback.timeout:
            self._user_feedback = None
            return None

        # Format the feedback
        action = self._user_feedback.action
        description = self._user_feedback.description
        feedback_type = self._user_feedback.feedback_type

        # Apply gradients based on the current theme and feedback type
        # Choose different gradient types based on feedback category
        gradient_type = "feedback"
        if feedback_type == FeedbackType.ERROR:
            gradient_type = "error"
        elif feedback_type == FeedbackType.SYSTEM:
            gradient_type = "system"

        styled_action = apply_gradient_to_text(action, gradient_type, bold=True)
        styled_description = create_subtle_gradient_text(description, gradient_type)

        return f"\n► {styled_action}: {styled_description}"

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
        position_info = f"[dim]Song {self._state.current_playlist_pos + 1} of {len(self._current_song_names)}[/dim]"
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
        if not self._history.loaded or self._history.play_count <= 1:
            return None

        # Format the play count with appropriate styling and gradients
        style = get_gradient_style()

        if self._history.category == HistoryCategory.FAVORITE:
            count_text = apply_gradient_to_text(
                f"You've played this {self._history.play_count} times!",
                "history",
                bold=True,
            )
        elif self._history.category == HistoryCategory.REGULAR:
            count_text = apply_gradient_to_text(
                f"You've played this {self._history.play_count} times", "history"
            )
        elif self._history.category == HistoryCategory.OCCASIONAL:
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
        self, action: str, description: str, timeout: float = 1.5
    ) -> None:
        """
        Show user feedback for an action in the UI.

        Args:
            action: Short name of the action
            description: Longer description of what happened
            timeout: How long to show the feedback (seconds)
        """
        should_show_feedback = (
            True if PLAYERSETTINGS.user_feedback_visible == "yes" else False
        )

        if should_show_feedback:
            self._user_feedback = UserFeedback(
                action=action,
                description=description,
                timestamp=time.time(),
                timeout=timeout,
            )

    def _get_user_feedback_text(self) -> Optional[str]:
        """
        Get formatted user feedback text with gradient effect.

        Returns:
            Formatted feedback text or None if no feedback to show
        """
        if not self._user_feedback:
            return None

        # Check if feedback has expired
        elapsed = time.time() - self._user_feedback.timestamp
        if elapsed > self._user_feedback.timeout:
            self._user_feedback = None
            return None

        # Format the feedback with gradients
        action = self._user_feedback.action
        description = self._user_feedback.description

        # Apply gradients based on the current theme
        styled_action = apply_gradient_to_text(action, "feedback", bold=True)
        styled_description = create_subtle_gradient_text(description, "feedback")

        return f"\n󰧂 {styled_action}: {styled_description}"

    def _get_status_text(self) -> str:
        """
        Get the current player status text with subtle gradient effects.

        Returns:
            Formatted status text
        """
        try:
            # Use our safe accessor to get pause state
            is_paused = self._is_paused()

            # Convert PlaybackState enum to string
            if self._state.playback_state == PlaybackState.PAUSED or is_paused:
                status = "Paused"
                self._state.playback_state = (
                    PlaybackState.PAUSED
                )  # Ensure enum is in sync
            elif self._state.playback_state == PlaybackState.PLAYING and not is_paused:
                status = "Playing"
            else:
                status = "Stopped"

            # Get volume safely using our _safe_get_property method instead of direct access
            vol = self._safe_get_property("volume", 0)
            if vol is None:
                vol = 0

            theme_info = (
                f" · Theme: {self._state.current_theme}"
                if self._state.current_theme
                else ""
            )

            # Apply subtle gradient to the status text
            status_text = create_subtle_gradient_text(
                f"Status: {status} · Volume: {vol}%{theme_info}", "status"
            )
            return f"[dim]{status_text}[/dim]"
        except ShutdownError:
            self._state.stop_requested = True
            self._state.playback_state = PlaybackState.STOPPED
            return "[dim]Status: Stopped[/dim]"
        except Exception as e:
            logger.error(f"Error getting status text: {e}")
            return "[dim]Status: Unknown[/dim]"

    # Replace direct property access with safe access
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
            BarColumn(bar_width=30, style=bar_color, complete_style=complete_color),
            TextColumn("[bold cyan]{task.fields[time]} / {task.fields[duration]}"),
        )

        # Get playback status text
        try:
            # Use the state instead of property access
            play_status = (
                "[red] PAUSED[/red]"
                if self._state.playback_state == PlaybackState.PAUSED
                else " PLAYING"
            )
        except Exception as e:
            logger.error(f"Error getting playback status: {e}")
            play_status = " UNKNOWN"

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
                self.unobserve_property("pause", self._on_pause_change)
                self.unobserve_property("duration", self._on_duration_change)
                self.unobserve_property("metadata", self._on_metadata_change)
                self.unobserve_property("playlist-pos", self._on_playlist_pos_change)
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
