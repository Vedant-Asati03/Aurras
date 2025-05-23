"""
Backup Manager for Aurras.

This module provides the main backup manager class for creating and managing backups.
"""

import time
import json
from pathlib import Path
from datetime import datetime

from aurras.utils.console import console
from aurras.core.settings import SETTINGS
from aurras.utils.logger import get_logger
from aurras.utils.path_manager import _path_manager

from aurras.core.backup.storage import LocalStorageBackend
from aurras.core.backup.utils import create_backup_id, get_readable_size

logger = get_logger("aurras.core.backup.manager", log_to_console=False)
BACKUP_SETTINGS = SETTINGS.backup
TIMED_BACKUP_SETTINGS = BACKUP_SETTINGS.timed_backup
ITEMS_BACKUP_SETTINGS = BACKUP_SETTINGS.backup_items


class BackupManager:
    """Main manager for the backup system."""

    def __init__(self):
        """Initialize the backup manager."""
        self.storage = LocalStorageBackend()

        self.last_backup_file = self.storage.metadata_dir / "last_backup.json"

    def _should_backup_automatically(self):
        """
        Check if an automatic backup is due.

        Returns:
            bool: True if backup is needed, False otherwise
        """
        # Check if timed backups are enabled
        if TIMED_BACKUP_SETTINGS.enable.lower() != "yes":
            return False

        # Check when the last backup was made
        if not self.last_backup_file.exists():
            return True  # No previous backup found

        try:
            with open(self.last_backup_file, "r") as f:
                last_backup_info = json.load(f)

            last_backup_time = last_backup_info.get("timestamp", 0)

            # Convert interval hours to seconds
            interval_seconds = TIMED_BACKUP_SETTINGS.interval * 60 * 60

            # Check if enough time has passed
            return (time.time() - last_backup_time) >= interval_seconds

        except Exception as e:
            logger.error(f"Error checking last backup time: {e}")
            return True  # If there's an error, assume backup is needed

    def check_and_backup(self):
        """
        Check if a backup is needed and perform it if so.

        Returns:
            bool: True if backup was created, False otherwise
        """
        if self._should_backup_automatically():
            try:
                return self.create_backup(show_message=False)
            except Exception as e:
                logger.error(f"Auto-backup failed: {e}")
                console.print_info(f"Auto-backup failed: {e}")
                return False

        return False

    def _get_files_to_backup(self):
        """
        Get a dictionary of files to back up based on settings.

        Returns:
            dict: Mapping of source paths to backup destinations
        """
        files_to_backup = {}

        backup_items = {
            "settings": (_path_manager.settings_file, "settings/settings.yaml"),
            "history": (_path_manager.history_db, "databases/history.db"),
            "playlists": (_path_manager.playlists_db, "databases/playlists.db"),
            "downloads": (_path_manager.downloads_db, "databases/downloads.db"),
            "cache": (_path_manager.cache_db, "databases/cache.db"),
            "credentials": (
                _path_manager.credentials_file,
                "credentials/credentials.json",
            ),
        }

        for key, (source_file_path, target_path) in backup_items.items():
            setting = getattr(ITEMS_BACKUP_SETTINGS, key, "yes").lower()
            if setting == "yes" and source_file_path.exists():
                files_to_backup[source_file_path] = target_path

        return files_to_backup

    def _cleanup_old_backups(self):
        """
        Remove old backups based on the maximum number of backups allowed.

        Returns:
            int: Number of backups removed
        """
        try:
            if int(BACKUP_SETTINGS.maximum_backups) > 0:
                removed = self.storage.cleanup_old_backups(
                    int(BACKUP_SETTINGS.maximum_backups)
                )
                if removed > 0:
                    console.print_info(f"Removed {removed} old backup(s)")

        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")
            console.print_error(f"Error cleaning up old backups: {e}")

    def create_backup(self, manual=False, show_message=True):
        """
        Create a backup of user data.

        Args:
            manual: Whether this is a manual backup request
            show_message: Whether to show status messages

        Returns:
            bool: True if successful, False otherwise
        """
        backup_id = create_backup_id()

        files_to_backup = self._get_files_to_backup()

        metadata = {
            "timestamp": time.time(),
            "date": datetime.now().isoformat(),
            "version": "1.1.1",  # Application version
            "manual": manual,
            "items": {},
        }

        # Track which items are included in the backup
        for item_name in [
            "settings",
            "history",
            "playlists",
            "downloads",
            "cache",
            "credentials",
        ]:
            setting_value = getattr(ITEMS_BACKUP_SETTINGS, item_name, "no").lower()
            metadata["items"][item_name] = setting_value == "yes"

        success = self.storage.save_backup(backup_id, files_to_backup, metadata)

        if success:
            with open(self.last_backup_file, "w") as f:
                json.dump({"timestamp": time.time(), "id": backup_id}, f)

            if show_message:
                backup_path = self.storage.backups_storage_dir / backup_id
                console.print_success(f"Backup created: {backup_path}")

            self._cleanup_old_backups()

        else:
            if show_message:
                console.print_error("Backup failed.")

        return success

    def delete_backup(self, backup_id):
        """
        Delete a backup by its ID.

        Args:
            backup_id (str): The ID of the backup to delete

        Returns:
            bool: True if successful, False otherwise
        """
        return self.storage.delete_backup(backup_id)

    def list_available_backups(self):
        """
        List all available backups with their details.

        Returns:
            list: List of backup info dictionaries
        """
        backups = self.storage.list_backups()

        if not backups:
            return []

        formatted_backups = []
        for i, backup in enumerate(backups, 1):
            try:
                metadata = backup["metadata"]
                date_str = metadata.get("date", "Unknown date")
                items = ", ".join(k for k, v in metadata.get("items", {}).items() if v)

                # Calculate size of backup directory
                backup_path = Path(backup["path"])
                size_bytes = sum(
                    f.stat().st_size for f in backup_path.glob("**/*") if f.is_file()
                )
                size_str = get_readable_size(size_bytes)

                formatted_backup = {
                    "index": i,
                    "id": backup["id"],
                    "path": backup_path,
                    "date": date_str,
                    "items": items,
                    "size": size_str,
                    "size_bytes": size_bytes,
                    "metadata": metadata,
                }

                formatted_backups.append(formatted_backup)
                console.print_success(
                    f"{i}. {backup['id']} [{date_str}] - {items} - {size_str}"
                )

            except Exception as e:
                logger.error(f"Error formatting backup {backup['id']}: {e}")
                console.print_error(f"Error reading backup {backup['id']}: {e}")

        return formatted_backups
