"""
Main Aurras TUI application.
"""

import logging

from textual.app import App, ComposeResult
from textual import work
from textual.binding import Binding
from textual.reactive import reactive
from textual.widgets import Header, Footer

try:
    from textual.command import ProviderSource

    HAS_NATIVE_COMMANDS = True
except ImportError:
    # Fall back to our custom implementation
    HAS_NATIVE_COMMANDS = False

from ..player.queue import QueueManager
from ..player.history import RecentlyPlayedManager
from ..playlist.manager import Select as PlaylistManager
from ..player.online import SongStreamHandler
from ..utils.path_manager import PathManager

from .screens.home import HomeScreen
from .screens.playlist import PlaylistScreen
from .screens.downloads import DownloadsScreen
from .screens.settings import SettingsScreen
from .commands import SongSearchProvider, CommandProvider, HelpProvider
from .themes.theme_manager import BUILTIN_THEMES, UserThemeLoadResult, load_user_themes

log = logging.getLogger("aurras.tui")
_path_manager = PathManager()


class AurrasTUI(App):
    """Aurras Terminal User Interface application."""

    COMMAND_PALETTE_BINDING = "slash"

    CSS_PATH = [
        "styles/variables.tcss",
        "styles/global.tcss",
        "styles/layout.tcss",
        "styles/components.tcss",
        "styles/panels.tcss",
        "styles/player.tcss",
        "styles/lists.tcss",
        "styles/palette.tcss",
        "styles/lyrics.tcss",
        "styles/search_palette.tcss",
    ]

    DEFAULT_BINDINGS = []

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", id="binding", show=True, priority=True),
        Binding("space", "toggle_play", "Play/Pause", id="binding", show=True),
        Binding("b", "next_song", "Next Song", id="binding", show=True),
        Binding("n", "previous_song", "Previous Song", id="binding", show=True),
        Binding("d", "push_screen('downloads')", "Downloads", id="binding", show=True),
    ]

    SCREENS = {
        "home": HomeScreen,
        "playlists": PlaylistScreen,
        "downloads": DownloadsScreen,
        "settings": SettingsScreen,
    }

    current_song = reactive("No song playing")
    is_playing = reactive(False)
    volume_level = reactive(70)
    current_theme_name = reactive("galaxy")

    COMMANDS: ProviderSource = [SongSearchProvider, CommandProvider, HelpProvider]

    def __init__(self):
        """Initialize the TUI application."""
        # IMPORTANT: Call super().__init__() first before setting any reactive properties
        super().__init__()
        self.themes = {}
        self._load_themes()

        for theme_name, theme in self.themes.items():
            self.register_theme(theme)

        if "galaxy" in self.themes:
            self.dark = BUILTIN_THEMES["galaxy"].dark
            self.current_theme_name = "galaxy"
            self.theme = "galaxy"

        self.queue_manager = QueueManager()
        self.history_manager = RecentlyPlayedManager()
        self.playlist_manager = PlaylistManager()

        self.command_mode = "command"  # Options: "search", "command", "options"

        self.active_palette = None

    def _load_themes(self) -> None:
        """Load built-in and user themes."""
        self.themes = dict(BUILTIN_THEMES)

        try:
            themes_dir = _path_manager.app_data_dir / "themes"
            themes_dir.mkdir(parents=True, exist_ok=True)

            user_themes_result: UserThemeLoadResult = load_user_themes(themes_dir)

            self.themes.update(user_themes_result.themes)

            for path, error in user_themes_result.failures:
                log.error(f"Failed to load theme {path}: {error}")

        except Exception as e:
            log.error(f"Error loading user themes: {e}")

    def compose(self) -> ComposeResult:
        """Compose the app layout."""
        yield Header()
        yield Footer(show_command_palette=False)

    def on_mount(self) -> None:
        """Handle app mount event."""
        self.push_screen("home")
        self.switch_theme(self.current_theme_name)

    def switch_theme(self, theme_name: str) -> None:
        """Switch to the specified theme."""
        if theme_name in self.themes:
            self.current_theme_name = theme_name

            if theme_name in BUILTIN_THEMES:
                self.dark = BUILTIN_THEMES[theme_name].dark

            # Set the theme by name (not the theme object)
            # This is critical for Textual's theme system to work properly
            self.theme = theme_name

            log.info(f"Switched to theme: {theme_name}")
        else:
            log.warning(f"Theme not found: {theme_name}")
            self.notify(f"Theme '{theme_name}' not found")

    def action_toggle_play(self) -> None:
        """Toggle play/pause."""
        self.is_playing = not self.is_playing

    def action_next_song(self) -> None:
        """Play next song."""
        next_song = self.queue_manager.get_next_song()
        if next_song:
            self.current_song = next_song

    def action_previous_song(self) -> None:
        """Play previous song."""
        previous = self.history_manager.get_previous_song()
        if previous:
            self.current_song = previous

    def action_volume_up(self) -> None:
        """Increase volume."""
        if self.volume_level < 100:
            self.volume_level += 5

    def action_volume_down(self) -> None:
        """Decrease volume."""
        if self.volume_level > 0:
            self.volume_level -= 5

    def _close_existing_palette(self) -> None:
        """Close any existing search palette."""
        if self.active_palette:
            try:
                self.active_palette.remove()
            except Exception:
                pass
            self.active_palette = None

    @work(thread=True)
    def _play_song(self, song_name: str) -> None:
        """Play a song in a background thread."""
        try:
            self.current_song = song_name
            self.is_playing = True

            if isinstance(self.screen, HomeScreen) and hasattr(
                self.screen, "_update_song_info"
            ):
                self.screen._update_song_info(song_name)

            player = SongStreamHandler(song_name)
            player.listen_song_online()

        except Exception as e:
            self.notify(f"Error playing song: {str(e)}")
            self.is_playing = False
