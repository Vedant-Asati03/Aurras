"""
Settings IO

This module provides functions for loading and saving settings from/to disk.
"""

import yaml

from .models import Settings
from ...utils.path_manager import PathManager

_path_manager = PathManager()


def load_settings() -> Settings:
    """Load settings from the settings file."""
    # First check if the settings file exists
    if not _path_manager.settings_file.exists():
        default_settings = Settings()
        save_settings(default_settings)
        return default_settings

    # Load from YAML file
    with open(_path_manager.settings_file, "r") as f:
        yaml_data = yaml.safe_load(f)

    return Settings.from_dict(yaml_data)


def save_settings(settings: Settings) -> None:
    """Save settings to YAML file."""
    _path_manager.settings_file.parent.mkdir(parents=True, exist_ok=True)
    with open(_path_manager.settings_file, "w") as f:
        yaml.dump(settings.to_dict(), f, default_flow_style=False, indent=4)


# Initialize settings when module is imported
default_settings = Settings()

# Ensure settings file exists
if not _path_manager.settings_file.exists():
    save_settings(default_settings)
