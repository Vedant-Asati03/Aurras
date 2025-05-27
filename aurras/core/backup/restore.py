"""
Restore functionality for Aurras backups.

This module provides the restoration functionality for Aurras backups,
including both standard restoration and smart media restoration.
"""

import time
import shutil
import sqlite3
from pathlib import Path

from aurras.utils.console import console
from aurras.utils.logger import get_logger
from aurras.utils.path_manager import _path_manager
from aurras.core.backup.manager import (
    BACKUP_SETTINGS,
    BackupItems,
    BackupPaths,
    THEMES_PATH,
)

logger = get_logger("aurras.core.backup.restore", log_to_console=False)


class RestoreManager:
    """Manager for restoring backups and media content."""

    def __init__(self, backup_manager):
        """
        Initialize the restore manager.

        Args:
            backup_manager: The backup manager instance
        """
        self.backup_manager = backup_manager
        self.storage = backup_manager.storage

    def list_available_backups(self):
        """
        List all available backups.

        Returns:
            list: List of backup info dictionaries
        """
        return self.backup_manager.list_available_backups()

    def restore_from_backup(self, backup_id=None):
        """
        Restore data from a backup.

        Args:
            backup_id: ID of the backup to restore from.
                      If None, the latest backup will be used.

        Returns:
            dict: Restoration result with success status and details
        """
        # Find the backup to restore
        if backup_id is None:
            backups = self.storage.list_backups()
            if not backups:
                console.print_info("No backup files found.")
                return {"success": False, "error": "No backup files found"}

            backup = backups[0]  # Latest backup
            backup_id = backup["id"]
        else:
            backup = self.storage.get_backup(backup_id)
            if not backup:
                console.print_warning(f"Backup not found: {backup_id}")
                return {"success": False, "error": f"Backup not found: {backup_id}"}

        backup_path = Path(backup["path"])
        console.print_success(f"Restoring from backup: {backup_id}")

        # Create a temporary directory for restoration
        temp_dir = _path_manager.construct_path("temp_restore")
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        temp_dir.mkdir(parents=True, exist_ok=True)

        restoration_result = {
            "success": False,
            "backup_id": backup_id,
            "restored_items": {},
            "needs_download": False,
            "download_items": [],
        }

        try:
            # Read metadata
            metadata = backup["metadata"]
            items = metadata.get("items", {})

            # Restore settings
            if items.get(BackupItems.SETTINGS.value, False):
                settings_path = backup_path / BackupPaths.SETTINGS.value
                if settings_path.exists():
                    shutil.copy(settings_path, _path_manager.settings_file)
                    console.print_success("Settings restored")
                    restoration_result["restored_items"]["settings"] = True

            # Restore custom themes
            if items.get(BackupItems.THEMES.value, False):
                themes_path = backup_path / BackupPaths.THEMES.value
                if themes_path.exists():
                    shutil.copy(themes_path, THEMES_PATH)
                    console.print_success("Custom themes restored")
                    restoration_result["restored_items"]["themes"] = True

            # Close any open database connections before restoring
            time.sleep(0.5)

            # Restore history database
            if items.get(BackupItems.HISTORY.value, False):
                history_path = backup_path / BackupPaths.HISTORY.value
                if history_path.exists():
                    shutil.copy(history_path, _path_manager.history_db)
                    console.print_success("Play history restored")
                    restoration_result["restored_items"]["history"] = True

            # Restore playlists database
            if items.get(BackupItems.PLAYLISTS.value, False):
                playlists_path = backup_path / BackupPaths.PLAYLISTS.value
                if playlists_path.exists():
                    shutil.copy(playlists_path, _path_manager.playlists_db)
                    console.print_success("Playlists restored")
                    restoration_result["restored_items"]["playlists"] = True

            # Restore downloads database
            if items.get(BackupItems.DOWNLOADS.value, False):
                downloads_path = backup_path / BackupPaths.DOWNLOADS.value
                if downloads_path.exists():
                    shutil.copy(downloads_path, _path_manager.downloads_db)
                    console.print_success("Downloads database restored")
                    restoration_result["restored_items"]["downloads_db"] = True

            # Restore cache if it was backed up
            if items.get(BackupItems.CACHE.value, False):
                cache_path = backup_path / BackupPaths.CACHE.value
                if cache_path.exists():
                    shutil.copy(cache_path, _path_manager.cache_db)
                    console.print_success("Cache restored")
                    restoration_result["restored_items"]["cache"] = True

            # Restore credentials
            if items.get(BackupItems.CREDENTIALS.value, False):
                credentials_dir = backup_path / BackupPaths.CREDENTIALS.value
                if credentials_dir.exists() and credentials_dir.is_dir():
                    _path_manager.credentials_dir.mkdir(parents=True, exist_ok=True)
                    for cred_file in credentials_dir.glob("*"):
                        if cred_file.is_file():
                            shutil.copy(
                                cred_file,
                                _path_manager.credentials_dir / cred_file.name,
                            )
                    console.print_success("Credentials restored")
                    restoration_result["restored_items"]["credentials"] = True

            # Check if smart restore is needed
            smart_restore_enabled = (
                BACKUP_SETTINGS.smart_restore.enable.lower() == "yes"
            )
            if smart_restore_enabled and restoration_result["restored_items"].get(
                "downloads_db", False
            ):
                # Check if there are missing downloaded files that need to be restored
                missing_downloads = self._check_missing_downloads()

                if missing_downloads:
                    restoration_result["needs_download"] = True
                    restoration_result["download_items"] = missing_downloads

                    # Show notification about smart restore option
                    redownload_strategy = (
                        BACKUP_SETTINGS.smart_restore.redownload_strategy.lower()
                    )

                    if redownload_strategy == "always":
                        console.print_info(
                            "Smart restore will download missing media files."
                        )
                        # Start smart restore process
                        self._perform_smart_restore(missing_downloads)
                    elif redownload_strategy == "ask":
                        console.print_info(
                            "Missing media files detected that need to be re-downloaded."
                        )
                        console.print_info(
                            "Use the 'smart_restore' command to restore them."
                        )
                    # For "never" strategy, we just include the info in the result

            console.print_success("Restoration completed successfully!")
            restoration_result["success"] = True
            return restoration_result

        except Exception as e:
            logger.error(f"Error during restoration: {e}")
            console.print_error(f"[red]Error during restoration: {e}[/red]")
            restoration_result["error"] = str(e)
            return restoration_result

        finally:
            # Clean up temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _check_missing_downloads(self):
        """
        Check for missing downloaded files based on the downloads database.

        Returns:
            list: List of missing download items
        """
        missing_downloads = []

        try:
            # Connect to the downloads database
            conn = sqlite3.connect(_path_manager.downloads_db)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Query for all downloaded items
            cursor.execute("SELECT * FROM downloads WHERE status='completed'")
            downloads = cursor.fetchall()

            for download in downloads:
                local_path = Path(download["local_path"])

                # Check if the file exists
                if not local_path.exists():
                    missing_downloads.append(
                        {
                            "id": download["id"],
                            "title": download["title"],
                            "artist": download["artist"],
                            "source_url": download["source_url"],
                            "local_path": download["local_path"],
                            "playlist_id": download.get("playlist_id"),
                        }
                    )

            conn.close()

            return missing_downloads

        except Exception as e:
            logger.error(f"Error checking missing downloads: {e}")
            return []

    def _perform_smart_restore(self, missing_downloads):
        """
        Perform smart restoration of missing media files.

        Args:
            missing_downloads: List of missing download items

        Returns:
            bool: True if successful, False otherwise
        """
        # This is a placeholder for the actual implementation
        # In a real implementation, this would use the downloader to re-download files

        console.print_info("Starting smart restoration of missing media files...")
        console.print_info(f"Found {len(missing_downloads)} files to restore.")

        # Placeholder for now - in a real implementation, this would:
        # 1. Group downloads by playlist for efficiency
        # 2. Create appropriate directories
        # 3. Use the app's downloader to fetch the files
        # 4. Show progress updates

        console.print_info("Smart restore functionality not fully implemented.")
        console.print_info("Would download the following files:")

        for i, item in enumerate(missing_downloads[:5], 1):
            console.print_info(f"{i}. {item['title']} by {item['artist']}")

        if len(missing_downloads) > 5:
            console.print_info(f"...and {len(missing_downloads) - 5} more files")

        return True

    def smart_restore(self, include_playlists=True, include_songs=True):
        """
        Perform smart restoration of missing media files.

        Args:
            include_playlists: Whether to restore playlist content
            include_songs: Whether to restore individual songs

        Returns:
            bool: True if successful, False otherwise
        """
        # Check if smart restore is enabled
        if BACKUP_SETTINGS.smart_restore.enable.lower() != "yes":
            console.print_info("Smart restore is disabled in settings.")
            return False

        missing_downloads = self._check_missing_downloads()

        if not missing_downloads:
            console.print_info("No missing media files to restore.")
            return True

        # Filter based on parameters
        if not include_playlists:
            missing_downloads = [
                d for d in missing_downloads if not d.get("playlist_id")
            ]

        if not include_songs:
            missing_downloads = [d for d in missing_downloads if d.get("playlist_id")]

        if not missing_downloads:
            console.print_info("No media files match the selected criteria.")
            return True

        # Perform smart restore
        return self._perform_smart_restore(missing_downloads)
