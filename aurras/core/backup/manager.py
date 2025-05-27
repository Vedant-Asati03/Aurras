"""
Backup Manager for Aurras.

This module provides the main backup manager class for creating and managing backups.
"""

import time
import json
from enum import Enum
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

from aurras import __version__
from aurras.utils.console import console
from aurras.core.settings import SETTINGS
from aurras.utils.logger import get_logger
from aurras.utils.path_manager import _path_manager

from aurras.core.backup.storage import LocalStorageBackend
from aurras.core.backup.utils import create_backup_id, get_readable_size

logger = get_logger("aurras.core.backup.manager", log_to_console=False)

# Constants
YES_VALUE = "yes"
NO_VALUE = "no"
THEMES_PATH = _path_manager.config_dir / "themes.yaml"
BACKUP_SETTINGS = SETTINGS.backup
TIMED_BACKUP_SETTINGS = BACKUP_SETTINGS.timed_backup
ITEMS_BACKUP_SETTINGS = BACKUP_SETTINGS.backup_items


class BackupItems(Enum):
    """Enum for backup items settings."""

    SETTINGS = "settings"
    THEMES = "themes"
    HISTORY = "history"
    PLAYLISTS = "playlists"
    DOWNLOADS = "downloads"
    CACHE = "cache"
    CREDENTIALS = "credentials"


class BackupPaths(Enum):
    """Enum for Paths where backups are stored."""

    SETTINGS = "config/settings.yaml"
    THEMES = "config/themes.yaml"
    HISTORY = "databases/history.db"
    PLAYLISTS = "databases/playlists.db"
    DOWNLOADS = "databases/downloads.db"
    CACHE = "databases/cache.db"
    CREDENTIALS = "credentials/credentials.json"


class BackupManager:
    """Main manager for the backup system."""

    def __init__(self):
        """Initialize the backup manager."""
        self.storage = LocalStorageBackend()
        self.last_backup_file = self.storage.metadata_dir / "last_backup.json"

    @property
    def backup_directory(self) -> Path:
        """Get the path to the backup directory."""
        return self.storage.backups_storage_dir

    def _is_setting_enabled(self, setting_value: str) -> bool:
        """
        Check if a setting is enabled.

        Args:
            setting_value: The value of the setting to check

        Returns:
            bool: True if the setting is enabled ('yes'), False otherwise
        """
        return setting_value.lower() == YES_VALUE

    def _should_backup_automatically(self) -> bool:
        """
        Check if an automatic backup is due.

        Returns:
            bool: True if backup is needed, False otherwise
        """
        # Check if timed backups are enabled
        if not self._is_setting_enabled(TIMED_BACKUP_SETTINGS.enable):
            return False

        # Check when the last backup was made
        if not self.last_backup_file.exists():
            logger.info("No previous backup found, scheduling backup")
            return True  # No previous backup found

        try:
            with open(self.last_backup_file, "r") as f:
                last_backup_info = json.load(f)

            last_backup_time = last_backup_info.get("timestamp", 0)

            # Convert interval hours to seconds
            interval_seconds = TIMED_BACKUP_SETTINGS.interval * 60 * 60

            # Check if enough time has passed
            time_since_backup = time.time() - last_backup_time
            is_backup_needed = time_since_backup >= interval_seconds

            if is_backup_needed:
                logger.info(
                    f"Backup interval reached ({time_since_backup / 3600:.1f} hours since last backup)"
                )

            return is_backup_needed

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in last backup file: {e}")
            return True
        except IOError as e:
            logger.error(f"Error reading last backup file: {e}")
            return True
        except Exception as e:
            logger.error(f"Unexpected error checking last backup time: {e}")
            return True  # If there's an error, assume backup is needed

    def check_and_backup(self) -> bool:
        """
        Check if a backup is needed and perform it if so.

        Returns:
            bool: True if backup was created, False otherwise
        """
        if not self._should_backup_automatically():
            logger.debug("Automatic backup not needed at this time")
            return False

        logger.info("Starting automatic backup")
        try:
            result = self.create_backup(show_message=False)
            if result:
                logger.info("Automatic backup completed successfully")
            else:
                logger.warning("Automatic backup failed")
            return result
        except Exception as e:
            logger.error(f"Auto-backup failed with exception: {e}")
            console.print_info(f"Auto-backup failed: {e}")
            return False

    def _get_files_to_backup(self) -> Dict[Path, str]:
        """
        Get a dictionary of files to back up based on settings.

        Returns:
            Dict[Path, str]: Mapping of source paths to backup destinations
        """
        files_to_backup = {}

        # Map each backup item to its source and destination paths
        backup_item_paths = {
            BackupItems.SETTINGS: (
                _path_manager.settings_file,
                BackupPaths.SETTINGS.value,
            ),
            BackupItems.THEMES: (THEMES_PATH, BackupPaths.THEMES.value)
            if THEMES_PATH.exists()
            else None,
            BackupItems.HISTORY: (_path_manager.history_db, BackupPaths.HISTORY.value),
            BackupItems.PLAYLISTS: (
                _path_manager.playlists_db,
                BackupPaths.PLAYLISTS.value,
            ),
            BackupItems.DOWNLOADS: (
                _path_manager.downloads_db,
                BackupPaths.DOWNLOADS.value,
            ),
            BackupItems.CACHE: (_path_manager.cache_db, BackupPaths.CACHE.value),
            BackupItems.CREDENTIALS: (
                _path_manager.credentials_file,
                BackupPaths.CREDENTIALS.value,
            ),
        }

        # For each backup item, check if it's enabled and the source file exists
        for item, paths in backup_item_paths.items():
            if paths is None:
                continue

            source_file_path, target_path = paths
            setting = getattr(ITEMS_BACKUP_SETTINGS, item.value, YES_VALUE).lower()

            if self._is_setting_enabled(setting) and source_file_path.exists():
                logger.debug(f"Adding {item.value} to backup list")
                files_to_backup[source_file_path] = target_path

        return files_to_backup

    def _cleanup_old_backups(self) -> Optional[int]:
        """
        Remove old backups based on the maximum number of backups allowed.

        Returns:
            Optional[int]: Number of backups removed, or None if an error occurred
        """
        try:
            max_backups = int(BACKUP_SETTINGS.maximum_backups)
            if max_backups <= 0:
                logger.debug("Backup cleanup skipped (maximum_backups <= 0)")
                return 0

            removed = self.storage.cleanup_old_backups(max_backups)
            if removed > 0:
                logger.info(f"Removed {removed} old backup(s)")
                console.print_info(f"Removed {removed} old backup(s)")
            return removed

        except ValueError as e:
            logger.error(f"Invalid maximum_backups setting: {e}")
            console.print_error("Error cleaning up old backups: invalid setting")
            return None
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")
            console.print_error(f"Error cleaning up old backups: {e}")
            return None

    def create_backup(self, manual: bool = False, show_message: bool = True) -> bool:
        """
        Create a backup of user data.

        Args:
            manual: Whether this is a manual backup request
            show_message: Whether to show status messages

        Returns:
            bool: True if successful, False otherwise
        """
        backup_id = create_backup_id()
        logger.info(f"Starting backup creation: {backup_id} (manual={manual})")

        files_to_backup = self._get_files_to_backup()
        if not files_to_backup:
            logger.warning("No files to backup - check settings and file existence")
            if show_message:
                console.print_error(
                    "No files to backup. Check settings and file existence."
                )
            return False

        metadata = {
            "timestamp": time.time(),
            "date": datetime.now().isoformat(),
            "version": __version__,
            "manual": manual,
            "items": {},
        }

        # Populate metadata with enabled backup items
        for item_name in ITEMS_BACKUP_SETTINGS.__annotations__.keys():
            setting_value = getattr(ITEMS_BACKUP_SETTINGS, item_name, NO_VALUE).lower()
            is_enabled = self._is_setting_enabled(setting_value)

            if not THEMES_PATH.exists() and item_name == "themes":
                is_enabled = False

            metadata["items"][item_name] = is_enabled

        success = self.storage.save_backup(backup_id, files_to_backup, metadata)

        if success:
            logger.info(f"Backup created successfully: {backup_id}")

            try:
                with open(self.last_backup_file, "w") as f:
                    json.dump({"timestamp": time.time(), "id": backup_id}, f)
            except Exception as e:
                logger.error(f"Error saving last backup info: {e}")
                # Continue since the main backup was successful

            if show_message:
                backup_path = self.backup_directory / backup_id
                console.print_success(f"Backup created: {backup_path}")

            self._cleanup_old_backups()
        else:
            logger.error(f"Backup creation failed: {backup_id}")
            if show_message:
                console.print_error("Backup failed.")

        return success

    def delete_backup(self, backup_id: str) -> bool:
        """
        Delete a backup by its ID.

        Args:
            backup_id: The ID of the backup to delete

        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Deleting backup: {backup_id}")
        success = self.storage.delete_backup(backup_id)

        if success:
            logger.info(f"Successfully deleted backup: {backup_id}")
        else:
            logger.warning(f"Failed to delete backup: {backup_id}")

        return success

    def list_available_backups(self) -> List[Dict]:
        """
        List all available backups with their details.

        Returns:
            List[Dict]: List of backup info dictionaries
        """
        logger.debug("Listing available backups")
        backups = self.storage.list_backups()

        if not backups:
            logger.info("No backups found")
            return []

        formatted_backups = []
        for i, backup in enumerate(backups, 1):
            try:
                backup_id = backup.get("id", "unknown")
                metadata = backup["metadata"]
                date_str = metadata.get("date", "Unknown date")

                # Get list of backed up items
                items = ", ".join(k for k, v in metadata.get("items", {}).items() if v)

                # Calculate size of backup directory
                backup_path = Path(backup["path"])

                # Use a safer approach to calculate size
                size_bytes = 0
                try:
                    size_bytes = sum(
                        f.stat().st_size
                        for f in backup_path.glob("**/*")
                        if f.is_file()
                    )
                except PermissionError as e:
                    logger.warning(
                        f"Permission error calculating size for {backup_id}: {e}"
                    )
                except Exception as e:
                    logger.warning(f"Error calculating size for {backup_id}: {e}")

                size_str = get_readable_size(size_bytes)

                formatted_backup = {
                    "index": i,
                    "id": backup_id,
                    "path": backup_path,
                    "date": date_str,
                    "items": items,
                    "size": size_str,
                    "size_bytes": size_bytes,
                    "metadata": metadata,
                    "is_manual": metadata.get("manual", False),
                    "version": metadata.get("version", "unknown"),
                }

                formatted_backups.append(formatted_backup)
                console.print_success(
                    f"{i}. {backup_id} [{date_str}] - {items} - {size_str}"
                )

            except KeyError as e:
                logger.error(f"Missing required field in backup data: {e}")
                console.print_error(
                    f"Error reading backup {backup.get('id', 'unknown')}: missing data"
                )
            except Exception as e:
                backup_id = backup.get("id", "unknown")
                logger.error(f"Error formatting backup {backup_id}: {e}")
                console.print_error(f"Error reading backup {backup_id}: {e}")

        logger.info(f"Found {len(formatted_backups)} backups")
        return formatted_backups
