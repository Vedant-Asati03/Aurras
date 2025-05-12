"""
Settings Package

This module provides functionality for loading and creating default settings
with Pydantic for validation.

This package has been refactored from a single file into a structured module
for better organization and maintainability.
"""

from aurras.core.settings.models.base import Settings

# Create a default settings instance
default_settings = Settings()


from aurras.core.settings.io import load_settings, save_settings

# Global settings instance - load it once when the module is imported
SETTINGS = load_settings()

from aurras.core.settings.updater import SettingsUpdater

__all__ = [
    "save_settings",
    "default_settings",
    "SettingsUpdater",
    "SETTINGS",
]
