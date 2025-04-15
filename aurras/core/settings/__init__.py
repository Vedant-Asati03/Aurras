"""
Settings Package

This module provides functionality for loading and creating default settings
with Pydantic for validation.

This package has been refactored from a single file into a structured module
for better organization and maintainability.
"""

from .updater import SettingsUpdater
from .io import load_settings, save_settings, default_settings
from .models import (
    Settings,
    KeyboardShortcuts,
    BackupItems,
    TimedBackup,
    ManualBackup,
    Backup,
    AVAILABLE_THEMES,
)

__all__ = [
    "Settings",
    "KeyboardShortcuts",
    "BackupItems",
    "TimedBackup",
    "ManualBackup",
    "Backup",
    "AVAILABLE_THEMES",
    "load_settings",
    "save_settings",
    "default_settings",
    "SettingsUpdater",
]
