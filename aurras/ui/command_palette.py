import yaml
import questionary
from prompt_toolkit import prompt
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.box import ROUNDED

# Replace absolute import with relative import
from ..utils.path_manager import PathManager

_path_manager = PathManager()

from ..core.settings import LoadDefaultSettings, UpdateSpecifiedSettings
from ..utils.backup_manager import BackupManager  # Add this import


class CommandPalette:
    """Main class for the Aurras command palette interface."""

    def __init__(self):
        """Initialize the command palette."""
        self.console = Console()
        self.settings_display = DisplaySettings()

        # Define all available command palette actions
        self.commands = {
            "settings": {
                "name": "Settings",
                "description": "View and modify Aurras settings",
                "action": self.settings_display.display_settings,
            },
            "toggle_lyrics": {
                "name": "Toggle Lyrics Display",
                "description": "Turn lyrics display on or off",
                "action": self._toggle_lyrics,
            },
            "toggle_backup": {  # Add new command
                "name": "Toggle Backup System",
                "description": "Enable or disable automatic backups",
                "action": self._toggle_backup,
            },
            "create_backup": {  # Add new command
                "name": "Create Manual Backup",
                "description": "Create a backup of your settings and data",
                "action": self._create_manual_backup,
            },
            "restore_backup": {  # Add new command
                "name": "Restore from Backup",
                "description": "Restore settings and data from a backup",
                "action": self._restore_from_backup,
            },
            "clear_history": {
                "name": "Clear Play History",
                "description": "Delete all play history records",
                "action": self._clear_history,
            },
            "cleanup_cache": {
                "name": "Clean Up Cache",
                "description": "Remove old cached data to free space",
                "action": self._cleanup_cache,
            },
            "about": {
                "name": "About Aurras",
                "description": "Display information about Aurras",
                "action": self._show_about,
            },
            "setup_spotify": {
                "name": "Setup Spotify",
                "description": "Configure Spotify API credentials",
                "action": self._setup_spotify,
                "category": "Services",
            },
        }

    def show_command_palette(self):
        """Display the command palette and execute the selected command."""
        # Create choices for questionary
        choices = [
            f"{cmd['name']}: {cmd['description']}"
            for cmd_id, cmd in self.commands.items()
        ]

        # Add a cancel option
        choices.append("Cancel: Return to main interface")

        # Show command palette menu
        selected = questionary.select(
            "Command Palette",
            choices=choices,
        ).ask()

        if selected and not selected.startswith("Cancel"):
            # Extract command name from selection
            command_name = selected.split(":", 1)[0].strip()
            self.execute_command(command_name)

    def execute_command(self, command_name):
        """Execute a command by name."""
        # Find and execute the corresponding command
        for cmd_id, cmd in self.commands.items():
            if cmd["name"] == command_name:
                self.console.print(f"[bold cyan]Executing:[/bold cyan] {cmd['name']}")
                cmd["action"]()
                return True

        self.console.print(f"[bold red]Unknown command:[/bold red] {command_name}")
        return False

    def _toggle_lyrics(self):
        """Toggle the lyrics display setting."""
        settings_updater = UpdateSpecifiedSettings("show-lyrics")
        current = settings_updater.settings.get("show-lyrics", "yes").lower()
        new_value = "no" if current == "yes" else "yes"
        settings_updater.update_specified_setting_directly(new_value)

        # Show confirmation
        status = "ON" if new_value == "yes" else "OFF"
        self.console.print(f"[green]Lyrics display turned {status}[/green]")

    def _toggle_backup(self):
        """Toggle automatic backup on/off."""
        settings_updater = UpdateSpecifiedSettings("backup")
        current = (
            settings_updater.settings.get("backup", {}).get("enabled", "yes").lower()
        )
        new_value = "no" if current == "yes" else "yes"

        # Get existing backup settings or create new ones
        backup_settings = settings_updater.settings.get("backup", {})
        backup_settings["enabled"] = new_value

        # Update the setting
        with open(_path_manager.settings_file, "w") as config_file:
            settings_updater.settings["backup"] = backup_settings
            yaml.dump(
                settings_updater.settings,
                config_file,
                default_flow_style=False,
                indent=4,
            )

        # Show confirmation
        status = "ON" if new_value == "yes" else "OFF"
        self.console.print(f"[green]Automatic backups turned {status}[/green]")

        # If enabling, ask about frequency
        if new_value == "yes":
            frequency = questionary.text(
                "How often should backups occur (in days)?", default="7"
            ).ask()

            try:
                days = int(frequency)
                if days > 0:
                    backup_settings["backup-frequency"] = str(days)
                    # Update again with new frequency
                    with open(_path_manager.settings_file, "w") as config_file:
                        settings_updater.settings["backup"] = backup_settings
                        yaml.dump(
                            settings_updater.settings,
                            config_file,
                            default_flow_style=False,
                            indent=4,
                        )
                    self.console.print(
                        f"[green]Backup frequency set to {days} days[/green]"
                    )
            except ValueError:
                self.console.print(
                    "[yellow]Invalid number, using default 7 days[/yellow]"
                )

    def _create_manual_backup(self):
        """Create a manual backup of user data."""
        backup_manager = BackupManager()
        backup_manager.create_backup(manual=True)

    def _restore_from_backup(self):
        """Restore data from a backup."""
        backup_manager = BackupManager()

        # List available backups
        self.console.print("[cyan]Available backups:[/cyan]")
        backups = backup_manager.list_available_backups()

        if not backups:
            return

        # Ask which backup to restore
        choice = questionary.text(
            "Enter backup number to restore (or press Enter to cancel):", default=""
        ).ask()

        if not choice:
            self.console.print("[yellow]Restoration cancelled[/yellow]")
            return

        try:
            index = int(choice) - 1
            if 0 <= index < len(backups):
                # Confirm restoration
                confirm = questionary.confirm(
                    "This will overwrite your current settings and data. Continue?",
                    default=False,
                ).ask()

                if confirm:
                    backup_file = backups[index]["file"]
                    backup_manager.restore_from_backup(backup_file)
                else:
                    self.console.print("[yellow]Restoration cancelled[/yellow]")
            else:
                self.console.print("[red]Invalid backup number[/red]")
        except ValueError:
            self.console.print("[red]Invalid input. Please enter a number.[/red]")

    def _clear_history(self):
        """Clear the play history."""
        from ..player.history import RecentlyPlayedManager

        history_manager = RecentlyPlayedManager()

        # Confirm before clearing
        confirm = questionary.confirm(
            "Are you sure you want to clear your entire play history?"
        ).ask()
        if confirm:
            with self.console.status("[cyan]Clearing play history...[/cyan]"):
                history_manager.clear_history()
            self.console.print("[green]Play history cleared successfully[/green]")

    def _cleanup_cache(self):
        """Clean up cached data."""
        from ..utils.cache_cleanup import cleanup_all_caches

        # Ask for how many days to keep
        days = questionary.text(
            "Keep cache newer than how many days?", default="30"
        ).ask()

        try:
            days_int = int(days)
            with self.console.status("[cyan]Cleaning up cache...[/cyan]"):
                results = cleanup_all_caches(days_int)

            # Show results
            total = sum(results.values())
            if total > 0:
                self.console.print(
                    f"[green]Removed {total} cache entries older than {days_int} days[/green]"
                )
                for cache_type, count in results.items():
                    if count > 0:
                        self.console.print(f"  - {cache_type.title()}: {count} entries")
            else:
                self.console.print("[green]Cache is already clean![/green]")
        except ValueError:
            self.console.print("[red]Please enter a valid number of days[/red]")

    def _show_about(self):
        """Show information about Aurras."""
        about_panel = Panel.fit(
            "\n[bold cyan]Aurras Music Player[/bold cyan]\n\n"
            "Version: 1.1.1\n\n"  # Update version here
            "[green]A high-end command line music player with streaming,[/green]\n"
            "[green]lyrics display, and playlist management capabilities.[/green]\n\n"
            "Created by: Vedant Asati\n"
            "GitHub: [link=https://github.com/vedant-asati03/Aurras]https://github.com/vedant-asati03/Aurras[/link]\n",
            title="About",
            border_style="bright_blue",
            padding=(1, 2),
        )
        self.console.print(about_panel)

    def _setup_spotify(self):
        """Set up Spotify API credentials."""
        from ..ui.command_handler import InputCases

        InputCases().setup_spotify()


class DisplaySettings(LoadDefaultSettings):
    """Class for displaying and updating settings through the command palette."""

    def __init__(self) -> None:
        """Initialize with settings data."""
        super().__init__()
        setting_keys, setting_values = self._retrieve_formatted_settings()
        self.formatted_choices = self._generate_formatted_choices(
            setting_keys, setting_values
        )
        self.console = Console()

    def display_settings(self):
        """Display settings and allow user to change them."""
        # Create a table to display current settings
        table = Table(title="Current Settings", box=ROUNDED, border_style="cyan")
        table.add_column("Setting", style="bold green")
        table.add_column("Value", style="cyan")

        for key, value in self.settings.items():
            if isinstance(value, dict):
                table.add_row(key, "[dim]<complex setting>[/dim]")
            else:
                table.add_row(key, str(value))

        self.console.print(table)

        # Let user select a setting to change
        selected_setting = self._select_setting_from_choices(self.formatted_choices)
        if not selected_setting:
            return

        selected_key = list(self.settings)[
            self.formatted_choices.index(selected_setting)
        ]

        self._update_selected_setting(selected_key)

    def _update_selected_setting(self, setting_key):
        """Update the selected setting with user input."""
        current_value = self.settings[setting_key]

        # If it's a complex setting (dictionary), show a message
        if isinstance(current_value, dict):
            self.console.print(
                "[yellow]Complex settings can't be edited directly.[/yellow]"
            )
            return

        # Get user input for the new value
        new_value = questionary.text(
            f"Enter new value for '{setting_key}' (current: {current_value}):",
            default=str(current_value),
        ).ask()

        # Update the setting if user provided input
        if new_value is not None:
            updater = UpdateSpecifiedSettings(setting_key)
            updater.update_specified_setting_directly(new_value)
            self.console.print(
                f"[green]Setting '{setting_key}' updated to: {new_value}[/green]"
            )

    def _retrieve_formatted_settings(self):
        """Get formatted lists of setting keys and values."""
        keys = list(self.settings)
        values = [
            value if not isinstance(value, dict) else "<complex>"
            for value in self.settings.values()
        ]
        return keys, values

    def _generate_formatted_choices(self, keys: list, values: list):
        """Format settings as choices for the selection menu."""
        return [f"{key:<30} {value}" for key, value in zip(keys, values)]

    def _select_setting_from_choices(self, formatted_choices):
        """Let user select a setting from the list."""
        return questionary.select(
            "Select a setting to change (or ESC to cancel):", choices=formatted_choices
        ).ask()
