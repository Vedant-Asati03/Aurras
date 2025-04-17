"""
Display processor for Aurras CLI.

This module handles display-related commands and operations such as
toggling lyrics display, setting visualization options, and other UI preferences.
"""

import logging
from typing import Optional

from rich.console import Console

from ....core.settings import SettingsUpdater
from ...theme_helper import ThemeHelper, with_error_handling

logger = logging.getLogger(__name__)
console = Console()


class DisplayProcessor:
    """Handle display-related commands and operations."""

    def __init__(self):
        """Initialize the display processor."""
        pass

    @with_error_handling
    def toggle_lyrics(self, display_name: Optional[str] = None) -> int:
        """
        Toggle lyrics display on/off.

        Args:
            display_name: Optional display name for the setting

        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        if display_name is None:
            display_name = "Lyrics Display"

        settings_updater = SettingsUpdater("display-lyrics")
        current = settings_updater.previous_setting.lower()
        new_value = "no" if current == "yes" else "yes"
        settings_updater.update_specified_setting_directly(new_value)

        # Show confirmation with theme-consistent styling
        status = "ON" if new_value == "yes" else "OFF"
        success_color = ThemeHelper.get_theme_color("success", "green")
        console.print(
            f"[bold {success_color}]{display_name} turned {status}[/bold {success_color}]"
        )
        return 0

    @with_error_handling
    def toggle_visualization(self) -> int:
        """
        Toggle audio visualization on/off.

        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        settings_updater = SettingsUpdater("show-visualization")
        current = settings_updater.previous_setting.lower()
        new_value = "no" if current == "yes" else "yes"
        settings_updater.update_specified_setting_directly(new_value)

        # Show confirmation with theme-consistent styling
        status = "ON" if new_value == "yes" else "OFF"
        success_color = ThemeHelper.get_theme_color("success", "green")
        console.print(
            f"[bold {success_color}]Audio visualization turned {status}[/bold {success_color}]"
        )
        return 0

    @with_error_handling
    def toggle_notifications(self) -> int:
        """
        Toggle desktop notifications on/off.

        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        settings_updater = SettingsUpdater("enable-notifications")
        current = settings_updater.previous_setting.lower()
        new_value = "no" if current == "yes" else "yes"
        settings_updater.update_specified_setting_directly(new_value)

        # Show confirmation with theme-consistent styling
        status = "ON" if new_value == "yes" else "OFF"
        success_color = ThemeHelper.get_theme_color("success", "green")
        console.print(
            f"[bold {success_color}]Desktop notifications turned {status}[/bold {success_color}]"
        )
        return 0

    @with_error_handling
    def toggle_dark_mode(self) -> int:
        """
        Toggle dark mode on/off.

        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        settings_updater = SettingsUpdater("dark-mode")
        current = settings_updater.previous_setting.lower()
        new_value = "no" if current == "yes" else "yes"
        settings_updater.update_specified_setting_directly(new_value)

        # Show confirmation with theme-consistent styling
        mode = "Dark" if new_value == "yes" else "Light"
        success_color = ThemeHelper.get_theme_color("success", "green")
        console.print(
            f"[bold {success_color}]Switched to {mode} mode[/bold {success_color}]"
        )

        # Suggest reload
        console.print(
            "You may need to restart Aurras for this change to take full effect"
        )
        return 0


# Instantiate processor for direct import
processor = DisplayProcessor()
