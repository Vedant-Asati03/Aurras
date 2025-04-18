"""
Base Settings Model

This module defines the main Settings class that contains all application settings.
It provides a centralized Pydantic model for configuration management with proper
validation, type conversion, and serialization to/from YAML configuration files.
"""

from typing import Dict, Any
from pydantic import BaseModel, Field, field_validator

from .backup import Backup
from .validators import validate_volume
from .command import CommandSettings
from .shorthand import ShortHandSettings
from .keyboard import KeyboardShortcuts
from .appearance import AppearanceSettings
from .utils import dict_to_kebab_case, dict_to_snake_case
from ....utils.path_manager import PathManager

_path_manager = PathManager()


class Settings(BaseModel):
    # Playback settings
    maximum_volume: str = "130"
    default_volume: str = "100"

    # Authentication
    require_authentication: str = "yes"
    automatic_authentication: str = "yes"
    authentication_timeout_seconds: str = "7200"

    # Download settings
    playlist_path: str = str(_path_manager.playlists_dir)
    download_path: str = str(_path_manager.downloaded_songs_dir)
    download_format: str = "mp3"
    download_bitrate: str = "auto"
    maximum_retries: str = "3"

    # Recommendation settings
    enable_recommendations: str = "yes"
    maximum_recommendations: str = "3"

    # Command settings
    command: CommandSettings = Field(default_factory=CommandSettings)

    # Shorthand settings
    shorthand: ShortHandSettings = Field(default_factory=ShortHandSettings)

    # Keyboard shortcuts
    keyboard_shortcuts: KeyboardShortcuts = Field(default_factory=KeyboardShortcuts)

    # Appearance settings
    appearance_settings: AppearanceSettings = Field(default_factory=AppearanceSettings)

    # System settings
    enable_hardware_acceleration: str = "yes"
    enable_media_keys: str = "yes"
    enable_auto_updates: str = "yes"
    update_check_hours: str = "168"

    # Backup settings
    backup: Backup = Field(default_factory=Backup)

    # Advanced settings
    log_level: str = "info"
    buffer_size_kb: str = "4096"
    enable_cache: str = "yes"
    cache_limit_mb: str = "1024"
    automatic_cache_clearing: str = "yes"
    cache_expiry_days: str = "30"

    model_config = {"populate_by_name": True, "extra": "allow"}

    @field_validator("maximum_volume", "default_volume", mode="before")
    @classmethod
    def validate_volume_field(cls, v):
        """Validate volume settings are within acceptable range."""
        return validate_volume(v)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert settings to dictionary with kebab-case keys for YAML.

        Returns:
            Dict containing all settings with kebab-case keys for serialization.
        """
        data = self.model_dump()

        return dict_to_kebab_case(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Settings":
        """
        Create Settings from dictionary with kebab-case keys.

        Args:
            data: Dictionary containing settings with kebab-case keys

        Returns:
            Settings object with all configuration loaded.
        """
        return cls.model_validate(dict_to_snake_case(data))
