"""
Settings Module

This module provides functionality for loading and creating default settings.
"""

import yaml
from pathlib import Path

# Replace absolute import
from ..utils.path_manager import PathManager

_path_manager = PathManager()

# Default settings as a dictionary
default_settings = {
    "max-volume": "130",
    "show-video": "no",
    "show-lyrics": "yes",
    "authenticated": "yes",
    "keyboard-shortcuts": {
        "end-song": "q",
        "pause": "p",
        "translate-lyrics": "t",
    },
    "backup": {
        "auto-backup": "on",
        "manual-backup": {
            "status": "off",
            "timed": {
                "status": "off",
                "daily": "off",
                "weekly": "off",
                "monthly": "off",
            },
        },
    },
}


class LoadDefaultSettings:
    """Class for loading default settings from the settings file."""

    def __init__(self) -> None:
        """Initialize with loaded settings."""
        self.settings = self.load_default_settings()

    def load_default_settings(self):
        """Load settings from the settings file."""
        if not _path_manager.settings_file.exists():
            # Create default settings if file doesn't exist
            self.create_default_settings()

        with open(_path_manager.settings_file, "r") as default_settings_file:
            settings_data = yaml.safe_load(default_settings_file)

        return settings_data

    def create_default_settings(self):
        """Create the default settings file."""
        _path_manager.settings_file.parent.mkdir(parents=True, exist_ok=True)

        with open(_path_manager.settings_file, "w") as config_file:
            yaml.dump(default_settings, config_file, default_flow_style=False, indent=4)

    def reset_default_settings(self):
        """Reset settings to default values."""
        self.create_default_settings()


class UpdateSpecifiedSettings(LoadDefaultSettings):
    """Class for updating specific settings in the settings file."""

    def __init__(self, setting_to_edit) -> None:
        """Initialize with the setting to edit."""
        super().__init__()
        self.user_edit = None
        self.setting_to_edit = setting_to_edit
        self.previous_setting = self.settings.get(self.setting_to_edit, "")

    def _get_user_edit(self):
        """Get user input for the setting change."""
        # Using direct input since we might not have prompt_toolkit imported here
        self.user_edit = (
            input(f"Enter new value for {self.setting_to_edit}: ").strip().lower()
        )

    def update_specified_setting_through_user(self):
        """Update a specific setting based on user input."""
        self._get_user_edit()
        self.update_specified_setting_directly(self.user_edit)

    def update_specified_setting_directly(self, updated_setting: str):
        """Update a specific setting with the provided value."""
        with open(_path_manager.settings_file, "w") as config_file:
            self.settings[self.setting_to_edit] = (
                updated_setting if updated_setting else self.previous_setting
            )

            yaml.dump(
                self.settings,
                config_file,
                default_flow_style=False,
                indent=4,
            )
