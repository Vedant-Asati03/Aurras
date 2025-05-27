"""
Backup Models

This module defines the Pydantic models for backup-related configuration.
"""

from pydantic import BaseModel, Field


class BackupItems(BaseModel):
    """Items to include in backups."""

    cache: str = "yes"  # Cache data (can be regenerated)
    history: str = "yes"  # Playback history
    credentials: str = "yes"  # API credentials and tokens
    settings: str = "yes"  # User preferences and configurations
    themes: str = "yes" # Custom themes and styles
    downloads: str = "yes"  # Actual downloaded media files
    playlists: str = "yes"  # Playlist structure and metadata


class TimedBackup(BaseModel):
    """Configuration for timed backups."""

    enable: str = "yes"  # Enable timed backups
    interval: int = 24  # Interval in hours for backups


class SmartRestore(BaseModel):
    """Configuration for smart restoration of media files."""

    enable: str = "yes"  # Enable smart restore capability
    redownload_strategy: str = "ask"  # Options: "always", "ask", "never"


class BackupSettings(BaseModel):
    """Backup settings model."""

    # Backup directory path
    backup_dir: str = "default"  # 'default' uses platform-specific paths, otherwise absolute path to custom location
    # Windows: %LOCALAPPDATA%\aurras\backups
    # macOS: ~/Library/Application Support/aurras/backups
    # Linux: ~/.aurras/backups
    maximum_backups: int = 10  # Maximum number of backups to keep

    # Items to include in backups
    backup_items: BackupItems = Field(default_factory=BackupItems)

    # Timed backup settings
    timed_backup: TimedBackup = Field(default_factory=TimedBackup)

    # Smart restore settings
    smart_restore: SmartRestore = Field(default_factory=SmartRestore)

    model_config = {"extra": "allow"}
