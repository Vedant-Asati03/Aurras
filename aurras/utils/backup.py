"""
Backup Module

This module provides functionality for backing up user data.
"""

import shutil
import datetime
from pathlib import Path

from config.path import cache, saved_playlists, spotify_auth, recommendation
from aurras.utils.logger import debug_log


class BackupManager:
    """
    Class for managing backups of user data.
    """

    def __init__(self):
        """Initialize the BackupManager class."""
        self.backup_dir = Path.home() / ".aurras" / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self):
        """
        Create a backup of all important user data files.

        Returns:
            Path: The path to the created backup directory
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"backup_{timestamp}"
        backup_path.mkdir(parents=True, exist_ok=True)

        # Files to backup
        files_to_backup = [cache, saved_playlists, spotify_auth, recommendation]

        for file_path in files_to_backup:
            if file_path.exists():
                try:
                    shutil.copy2(file_path, backup_path)
                    debug_log(f"Backed up {file_path} to {backup_path}")
                except Exception as e:
                    debug_log(f"Failed to backup {file_path}: {str(e)}")

        return backup_path

    def restore_backup(self, backup_path):
        """
        Restore a backup from the specified path.

        Args:
            backup_path (Path): The path to the backup directory

        Returns:
            bool: True if the restore was successful, False otherwise
        """
        if not backup_path.exists():
            debug_log(f"Backup path {backup_path} does not exist")
            return False

        # Destination files
        dest_files = [cache, saved_playlists, spotify_auth, recommendation]

        success = True
        for dest_file in dest_files:
            source_file = backup_path / dest_file.name
            if source_file.exists():
                try:
                    shutil.copy2(source_file, dest_file)
                    debug_log(f"Restored {source_file} to {dest_file}")
                except Exception as e:
                    debug_log(f"Failed to restore {source_file}: {str(e)}")
                    success = False

        return success
