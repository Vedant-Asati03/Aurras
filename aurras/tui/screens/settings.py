"""
Settings screen for Aurras TUI.
"""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button, Switch, Input, Select
from textual.binding import Binding

from ..themes.theme_manager import BUILTIN_THEMES


class SettingsScreen(Screen):
    """Screen for configuring Aurras settings."""

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back"),
        Binding("s", "save_settings", "Save"),
        Binding("r", "reset_settings", "Reset"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the settings screen layout."""
        yield Header()

        with Container(id="settings-container"):
            yield Static("Settings", id="settings-title", classes="panel-title")

            with Vertical(id="settings-sections"):
                # Theme settings - put this first for visibility
                with Container(id="theme-settings", classes="settings-section"):
                    yield Static("Theme", classes="settings-section-title")

                    with Horizontal(classes="setting-row"):
                        yield Static("Theme:", classes="setting-label")
                        yield Select(
                            [(theme, theme) for theme in BUILTIN_THEMES.keys()],
                            value=self.app.current_theme_name
                            if hasattr(self.app, "current_theme_name")
                            else "galaxy",
                            id="theme",
                        )

                    with Horizontal(classes="setting-row"):
                        yield Static("Dark Mode:", classes="setting-label")
                        yield Switch(value=True, id="dark-mode")

                # Playback settings
                with Container(id="playback-settings", classes="settings-section"):
                    yield Static("Playback", classes="settings-section-title")

                    with Horizontal(classes="setting-row"):
                        yield Static("Show Video:", classes="setting-label")
                        yield Switch(value=False, id="show-video")

                    with Horizontal(classes="setting-row"):
                        yield Static("Show Lyrics:", classes="setting-label")
                        yield Switch(value=True, id="show-lyrics")

                    with Horizontal(classes="setting-row"):
                        yield Static("Max Volume:", classes="setting-label")
                        yield Input(value="130", id="max-volume")

                # Download settings
                with Container(id="download-settings", classes="settings-section"):
                    yield Static("Downloads", classes="settings-section-title")

                    with Horizontal(classes="setting-row"):
                        yield Static("Download Path:", classes="setting-label")
                        yield Input(value="~/Music/Aurras", id="download-path")

                    with Horizontal(classes="setting-row"):
                        yield Static("Download Format:", classes="setting-label")
                        yield Select(
                            [("MP3", "mp3"), ("FLAC", "flac"), ("WAV", "wav")],
                            value="mp3",
                            id="download-format",
                        )

                    with Horizontal(classes="setting-row"):
                        yield Static("Auto-download Lyrics:", classes="setting-label")
                        yield Switch(value=True, id="download-lyrics")

                # Backup settings
                with Container(id="backup-settings", classes="settings-section"):
                    yield Static("Backup", classes="settings-section-title")

                    with Horizontal(classes="setting-row"):
                        yield Static("Auto Backup:", classes="setting-label")
                        yield Switch(value=True, id="auto-backup")

                    with Horizontal(classes="setting-row"):
                        yield Static(
                            "Backup Frequency (days):", classes="setting-label"
                        )
                        yield Input(value="7", id="backup-frequency")

                    with Horizontal(classes="setting-row"):
                        yield Static("Backup Location:", classes="setting-label")
                        yield Input(value="default", id="backup-location")

            with Horizontal(id="settings-actions"):
                yield Button("Save", id="save-settings", variant="primary")
                yield Button("Reset", id="reset-settings")
                yield Button("Factory Reset", id="factory-reset")

        yield Footer()

    def on_mount(self):
        """Handle mounting of the settings screen."""
        self.app.sub_title = "Settings & Preferences"
        self._load_current_settings()

    def _load_current_settings(self):
        """Load current settings into the form."""
        try:
            # Load theme setting
            if hasattr(self.app, "current_theme_name"):
                theme_select = self.query_one("#theme", Select)
                theme_select.value = self.app.current_theme_name

            # Load volume setting
            if hasattr(self.app, "volume_level"):
                volume_input = self.query_one("#max-volume", Input)
                volume_input.value = str(self.app.volume_level)

            # TODO: Load other settings as they're implemented

        except Exception as e:
            self.notify(f"Error loading settings: {e}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id

        if button_id == "save-settings":
            self.action_save_settings()

        elif button_id == "reset-settings":
            self.action_reset_settings()

        elif button_id == "factory-reset":
            self._factory_reset()

    def on_select_changed(self, event):
        """Handle select field changes."""
        if event.select.id == "theme":
            self._preview_theme(event.select.value)

    def _preview_theme(self, theme_name):
        """Preview a theme when selected."""
        if hasattr(self.app, "switch_theme") and theme_name in BUILTIN_THEMES:
            self.app.switch_theme(theme_name)
            self.notify(f"Theme set to {theme_name}")

    def action_save_settings(self) -> None:
        """Save current settings."""
        try:
            # Read and save theme settings
            theme_select = self.query_one("#theme", Select)
            if hasattr(self.app, "switch_theme"):
                self.app.switch_theme(theme_select.value)

            # Read and save dark mode setting
            dark_mode = self.query_one("#dark-mode", Switch)
            # TODO: Implement saving dark mode setting

            # Read and save volume setting
            volume_input = self.query_one("#max-volume", Input)
            try:
                volume = int(volume_input.value)
                if hasattr(self.app, "volume_level"):
                    self.app.volume_level = min(130, max(0, volume))
            except ValueError:
                self.notify("Invalid volume value")

            # Read and save download settings
            download_path = self.query_one("#download-path", Input)
            # TODO: Implement saving download path

            download_format = self.query_one("#download-format", Select)
            # TODO: Implement saving download format

            # Save settings complete
            self.notify("Settings saved successfully")

        except Exception as e:
            self.notify(f"Error saving settings: {e}")

    def action_reset_settings(self) -> None:
        """Reset settings to their saved values."""
        self._load_current_settings()
        self.notify("Settings have been reset to saved values")

    def _factory_reset(self) -> None:
        """Reset all settings to factory defaults."""
        # Theme reset
        theme_select = self.query_one("#theme", Select)
        theme_select.value = "galaxy"
        if hasattr(self.app, "switch_theme"):
            self.app.switch_theme("galaxy")

        # Dark mode reset
        dark_mode = self.query_one("#dark-mode", Switch)
        dark_mode.value = True

        # Volume reset
        volume_input = self.query_one("#max-volume", Input)
        volume_input.value = "100"
        if hasattr(self.app, "volume_level"):
            self.app.volume_level = 100

        # Download path reset
        download_path = self.query_one("#download-path", Input)
        download_path.value = "~/Music/Aurras"

        # Download format reset
        download_format = self.query_one("#download-format", Select)
        download_format.value = "mp3"

        # Auto backup reset
        auto_backup = self.query_one("#auto-backup", Switch)
        auto_backup.value = True

        # Backup frequency reset
        backup_frequency = self.query_one("#backup-frequency", Input)
        backup_frequency.value = "7"

        # Backup location reset
        backup_location = self.query_one("#backup-location", Input)
        backup_location.value = "default"

        self.notify("All settings have been reset to factory defaults")
