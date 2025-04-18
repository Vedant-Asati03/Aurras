"""
Backup Models

This module defines the Pydantic models for backup-related configuration.
"""

from pydantic import BaseModel, Field


class BackupItems(BaseModel):
    history: str = "yes"
    playlists: str = "yes"
    settings: str = "yes"
    cache: str = "no"
    downloads: str = "no"

    model_config = {"extra": "allow"}


class TimedBackup(BaseModel):
    status: str = "off"
    daily: str = "off"
    weekly: str = "off"
    monthly: str = "off"

    model_config = {"extra": "allow"}


class ManualBackup(BaseModel):
    status: str = "off"
    timed: TimedBackup = Field(default_factory=TimedBackup)

    model_config = {"extra": "allow"}


class Backup(BaseModel):
    enable_backups: str = "yes"  # More consistent than "enabled"
    automatic_backups: str = "yes"  # More descriptive than "auto_backup"
    backup_interval_days: str = "7"  # Unit is now in the name
    backup_location: str = "default"
    backup_items: BackupItems = Field(default_factory=BackupItems)
    manual_backup: ManualBackup = Field(default_factory=ManualBackup)
    maximum_backups: str = "10"  # More consistent

    model_config = {"extra": "allow"}
