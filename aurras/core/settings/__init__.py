"""
Settings Package

This module provides functionality for loading and creating default settings
with Pydantic for validation.

This package has been refactored from a single file into a structured module
for better organization and maintainability.
"""

from aurras.utils.logger import get_logger
from aurras.core.settings.models.base import Settings

logger = get_logger("aurras.core.settings", log_to_console=False)

# Create a default settings instance
default_settings = Settings()


from aurras.core.settings.io import load_settings

# Global settings instance - load it once when the module is imported
SETTINGS = load_settings()
logger.debug("Settings loaded successfully")

from aurras.core.settings.updater import SettingsUpdater

__all__ = [
    "default_settings",
    "SettingsUpdater",
    "SETTINGS",
]
