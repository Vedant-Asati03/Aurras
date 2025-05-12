"""
Settings IO

This module provides functions for loading and saving settings from/to disk.
"""

import yaml

from aurras.core.settings import default_settings
from aurras.utils.path_manager import _path_manager

# Global settings instance (singleton)
_SETTINGS_INSTANCE = None


def load_settings():
    """
    Load settings from the settings file.

    Returns:
        Settings object loaded from file or default settings if file doesn't exist
    """
    global _SETTINGS_INSTANCE

    # Return cached instance if available
    if _SETTINGS_INSTANCE is not None:
        return _SETTINGS_INSTANCE

    # First check if the settings file exists
    if not _path_manager.settings_file.exists():
        save_settings(default_settings)
        return default_settings

    # Load from YAML file
    with open(_path_manager.settings_file, "r") as f:
        yaml_data = yaml.safe_load(f)

    _SETTINGS_INSTANCE = default_settings.from_dict(yaml_data)
    return _SETTINGS_INSTANCE


def save_settings(settings) -> None:
    """
    Save settings to YAML file and update the cached instance.

    Args:
        settings: Settings object to save
    """
    global _SETTINGS_INSTANCE

    # Ensure the settings directory exists
    _path_manager.settings_file.parent.mkdir(parents=True, exist_ok=True)

    # Save to YAML file
    with open(_path_manager.settings_file, "w") as f:
        yaml.dump(settings.to_dict(), f)

    # Update the cached instance
    _SETTINGS_INSTANCE = settings
