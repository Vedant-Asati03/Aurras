"""
Backup processor for Aurras CLI.

This module handles backup and restore commands for Aurras data,
including user preferences, playlists, history, and media files.
"""

from typing import Optional

from aurras.utils.console import console
from aurras.utils.logger import get_logger
from aurras.utils.decorators import with_error_handling
from aurras.core.settings import SETTINGS, SettingsUpdater
from aurras.core.backup import BackupManager, RestoreManager

logger = get_logger("aurras.command.processors.backup", log_to_console=False)


def set_setting_value(setting_key, value):
    """
    Set a setting value using the SettingsUpdater.

    Args:
        setting_key (str): The setting key in dot notation
        value: The value to set

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        updater = SettingsUpdater(setting_key)
        updater.new_value = value
        updater.apply_update()
        return True
    except Exception as e:
        logger.error(f"Failed to update setting {setting_key}: {e}")
        return False


class BackupProcessor:
    """Handle backup-related commands and operations."""

    def __init__(self):
        """Initialize the backup processor."""
        self.backup_manager = BackupManager()
        self.restore_manager = RestoreManager(self.backup_manager)

    @with_error_handling
    def create_backup(self, manual: bool = True) -> int:
        """
        Create a new backup of user data.

        Args:
            manual: Whether this is a manual backup (vs. automatic)

        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        success = self.backup_manager.create_backup(manual=manual)
        return 0 if success else 1

    @with_error_handling
    def delete_backup(self, backup_id: str) -> int:
        """
        Delete a specific backup.

        Args:
            backup_id: ID of the backup to delete.
                      If None, the user will be prompted to select one.

        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        if backup_id is None:
            console.print_warning("No backup ID provided. Please specify one.")
            return 1

        if not self.backup_manager.delete_backup(backup_id):
            console.print_error(f"Failed to delete backup {backup_id}.")
            return 1

        console.print_success(f"Backup {backup_id} deleted successfully.")
        return 0

    @with_error_handling
    def list_backups(self) -> int:
        """
        List all available backups.

        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        backups = self.backup_manager.list_available_backups()
        if not backups:
            console.print_info("No backups found.")

        return 0

    @with_error_handling
    def restore_backup(self, backup_id: Optional[str] = None) -> int:
        """
        Restore data from a backup.

        Args:
            backup_id: ID of the backup to restore from.
                      If None, the user will be prompted to select one.

        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        # If no backup_id provided, show a list and ask the user to select one
        if backup_id is None:
            backups = self.backup_manager.list_available_backups()

            if not backups:
                console.print_info("No backups found to restore from.")
                return 1

            # Ask the user to select a backup
            backup_index = console.prompt(
                "Select a backup to restore (number)",
                style_key="primary",
                default="1",
            )

            try:
                backup_index = int(backup_index) - 1  # Adjust for 0-based indexing
                if 0 <= backup_index < len(backups):
                    backup_id = backups[backup_index]["id"]
                else:
                    console.print_error(f"Invalid backup selection: {backup_index + 1}")
                    return 1
            except ValueError:
                console.print_error("Invalid input. Please enter a number.")
                return 1

        # Perform the restoration
        result = self.restore_manager.restore_from_backup(backup_id)

        if result["success"]:
            console.print_success("Backup restoration completed successfully!")

            # If smart restore is needed, offer to run it
            if result.get("needs_download", False):
                if SETTINGS.backup.smart_restore.redownload_strategy.lower() == "ask":
                    do_smart_restore = console.prompt(
                        "Restore missing media files? (yes/no)",
                        style_key="primary",
                        default="yes",
                    ).lower()

                    if do_smart_restore in ["yes", "y"]:
                        self.smart_restore()

            return 0
        else:
            console.print_error(
                f"Backup restoration failed: {result.get('error', 'Unknown error')}"
            )
            return 1

    @with_error_handling
    def smart_restore(
        self, include_playlists: bool = True, include_songs: bool = True
    ) -> int:
        """
        Perform smart restoration of missing media files.

        Args:
            include_playlists: Whether to restore playlist content
            include_songs: Whether to restore individual songs

        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        success = self.restore_manager.smart_restore(
            include_playlists=include_playlists, include_songs=include_songs
        )

        return 0 if success else 1
