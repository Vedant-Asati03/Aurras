"""
Application command provider for the command palette.
"""

from textual.command import Provider, Hit, DiscoveryHit
from rich.text import Text

from ...player.queue import QueueManager
from ..themes.theme_manager import BUILTIN_THEMES


class CommandProvider(Provider):
    """Provider that handles app commands."""

    async def search(self, query: str):
        """Search for commands matching the query."""
        # Only process queries that start with '>' prefix
        if not query.startswith(">"):
            return

        # Remove the prefix for matching
        query = query[1:].strip()

        # Define command list with more useful application commands
        commands = {
            # Settings and configuration
            "settings": (
                "Settings",
                "Configure application settings",
                self._open_settings,
            ),
            "toggle_lyrics": (
                "Toggle Lyrics",
                "Turn lyrics display on or off",
                self._toggle_lyrics_action,
            ),
            "toggle_backup": (
                "Toggle Backup",
                "Enable or disable automatic backups",
                self._toggle_backup,
            ),
            # Data management
            "clear_history": (
                "Clear History",
                "Delete all play history",
                self._clear_history,
            ),
            "cleanup_cache": (
                "Clean Up Cache",
                "Remove old cached data",
                self._cleanup_cache,
            ),
            "create_backup": (
                "Create Backup",
                "Create a manual backup",
                self._create_backup,
            ),
            "restore_backup": (
                "Restore Backup",
                "Restore from a backup",
                self._restore_backup,
            ),
            # Services
            "setup_spotify": (
                "Setup Spotify",
                "Configure Spotify integration",
                self._setup_spotify,
            ),
            # Playback
            "play": ("Play/Pause", "Toggle playback", self._play_pause_action),
            "queue": ("View Queue", "Show current song queue", self._view_queue_action),
            "clear_queue": (
                "Clear Queue",
                "Clear the song queue",
                self._clear_queue_action,
            ),
            # System
            "about": (
                "About Aurras",
                "Show information about Aurras",
                self._show_about,
            ),
            "quit": ("Quit", "Exit Aurras", self._quit_action),
        }

        # Add theme commands
        for theme_name in BUILTIN_THEMES.keys():
            commands[f"theme_{theme_name}"] = (
                f"Theme: {theme_name.title()}",
                f"Switch to the {theme_name} theme",
                lambda t=theme_name: self._set_theme(t),
            )

        # If query is empty (just ">"), show all commands
        if not query:
            for cmd_id, (name, description, action) in commands.items():
                # Create a hit with no highlighting for each command
                yield Hit(
                    score=1.0,  # High score to show all commands
                    match_display=Text.from_markup(f"{name}: {description}"),
                    command=action,
                    text=name,
                    help=description,
                )
            return

        # Match against query
        matcher = self.matcher(query)

        for cmd_id, (name, description, action) in commands.items():
            # Check various fields for matches
            cmd_score = matcher.match(cmd_id)
            name_score = matcher.match(name)
            desc_score = matcher.match(description)
            score = max(cmd_score, name_score, desc_score)

            if score > 0:
                # Create display text with highlighting
                display = matcher.highlight(f"{name}: {description}")

                # Create hit
                yield Hit(
                    score=score,
                    match_display=display,
                    command=action,
                    text=name,
                    help=description,
                )

    async def discover(self):
        """Return discovery commands."""
        # Return empty to hide commands from initial view
        # Only show commands when '>' is typed
        return

    # Command action methods
    def _open_settings(self):
        self.app.push_screen("settings")

    def _toggle_backup(self):
        self.app.notify("Toggle backup functionality not implemented in TUI")

    def _clear_history(self):
        from ...player.history import RecentlyPlayedManager

        history = RecentlyPlayedManager()
        history.clear_history()
        self.app.notify("Play history cleared")

    def _cleanup_cache(self):
        self.app.notify("Cleaning up cache...")

    def _create_backup(self):
        self.app.notify("Creating backup...")

    def _restore_backup(self):
        self.app.notify("Restore from backup not implemented in TUI")

    def _setup_spotify(self):
        self.app.notify("Spotify setup not implemented in TUI")

    def _show_about(self):
        version = "1.1.1"
        self.app.notify(f"Aurras Music Player v{version} - Created by Vedant Asati")

    def _play_pause_action(self):
        if hasattr(self.app, "action_toggle_play"):
            self.app.action_toggle_play()

    def _next_song_action(self):
        if hasattr(self.app, "action_next_song"):
            self.app.action_next_song()

    def _prev_song_action(self):
        if hasattr(self.app, "action_previous_song"):
            self.app.action_previous_song()

    def _view_queue_action(self):
        self.app.notify("Queue view not implemented yet")

    def _clear_queue_action(self):
        queue = QueueManager()
        queue.clear_queue()
        self.app.notify("Queue cleared")

    def _toggle_lyrics_action(self):
        if hasattr(self.app.screen, "action_toggle_lyrics_size"):
            self.app.screen.action_toggle_lyrics_size()

    def _settings_action(self):
        self.app.push_screen("settings")

    def _quit_action(self):
        self.app.exit()

    def _set_theme(self, theme_name: str):
        """Set the application theme."""
        try:
            self.app.notify(f"Switching to {theme_name} theme...")

            # Use the app's switch_theme method instead of setting theme directly
            # This ensures proper theme registration and handling
            if hasattr(self.app, "switch_theme"):
                self.app.switch_theme(theme_name)
            else:
                # Fallback in case switch_theme doesn't exist
                self.app.notify("Theme switching not supported in this version")
        except Exception as e:
            self.app.notify(f"Error setting theme: {str(e)}")
