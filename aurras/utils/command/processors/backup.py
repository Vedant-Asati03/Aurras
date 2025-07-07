"""
Backup processor for Aurras CLI.

This module handles backup and restore commands for Aurras data,
including user preferences, playlists, history, and media files.
"""

from aurras.utils.console import console
from aurras.core.settings import SETTINGS
from aurras.utils.logger import get_logger
from aurras.utils.decorators import with_error_handling
from aurras.core.backup import BackupManager, RestoreManager

logger = get_logger("aurras.command.processors.backup")


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
        with logger.operation_context(operation="backup_creation"):
            with logger.profile_context("backup_creation"):
                success = self.backup_manager.create_backup(manual=manual)

            if success:
                logger.info(
                    "Backup created successfully",
                    extra={"operation": "backup_creation", "manual": manual},
                )
            else:
                logger.error(
                    "Failed to create backup",
                    extra={"operation": "backup_creation", "manual": manual},
                )

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
        with logger.operation_context(operation="backup_deletion"):
            if backup_id is None:
                logger.warning(
                    "No backup ID provided for deletion",
                    extra={"operation": "backup_deletion"},
                )
                console.print_warning("No backup ID provided. Please specify one.")
                return 1

            if not self.backup_manager.delete_backup(backup_id):
                logger.error(
                    "Failed to delete backup",
                    extra={"operation": "backup_deletion", "backup_id": backup_id},
                )
                console.print_error(f"Failed to delete backup {backup_id}.")
                return 1

            logger.info(
                "Backup deleted successfully",
                extra={"operation": "backup_deletion", "backup_id": backup_id},
            )
            console.print_success(f"Backup {backup_id} deleted successfully.")
            return 0

    @with_error_handling
    def list_backups(self) -> int:
        """
        List all available backups.

        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        with logger.operation_context(operation="backup_listing"):
            backups = self.backup_manager.list_available_backups()

            logger.info(
                "Retrieved backup list",
                extra={
                    "operation": "backup_listing",
                    "backup_count": len(backups) if backups else 0,
                },
            )

            if not backups:
                console.print_info("No backups found.")

            return 0

    @with_error_handling
    def restore_backup(self, backup_id: str) -> int:
        """
        Restore data from a backup.

        Args:
            backup_id: ID of the backup to restore from.

        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        with logger.operation_context(operation="backup_restoration"):
            logger.info(
                "Starting backup restoration",
                extra={
                    "operation": "backup_restoration",
                    "backup_id": backup_id,
                },
            )

            with logger.profile_context("backup_restoration"):
                result = self.restore_manager.restore_from_backup(backup_id)

            if result["success"]:
                logger.info(
                    "Backup restoration completed successfully",
                    extra={
                        "operation": "backup_restoration",
                        "backup_id": backup_id,
                        "needs_download": result.get("needs_download", False),
                    },
                )
                console.print_success("Backup restoration completed successfully!")

                # If smart restore is needed, offer to run it
                if result.get("needs_download", False):
                    logger.debug(
                        "Backup restoration requires smart restore",
                        extra={
                            "operation": "backup_restoration",
                            "backup_id": backup_id,
                            "redownload_strategy": SETTINGS.backup.smart_restore.redownload_strategy.lower(),
                        },
                    )

                    if (
                        SETTINGS.backup.smart_restore.redownload_strategy.lower()
                        == "ask"
                    ):
                        do_smart_restore = console.prompt(
                            "Restore missing media files? (yes/no)",
                            style_key="primary",
                            default="yes",
                        ).lower()

                        if do_smart_restore in ["yes", "y"]:
                            logger.info(
                                "User opted for smart restore",
                                extra={
                                    "operation": "backup_restoration",
                                    "backup_id": backup_id,
                                },
                            )
                            self.smart_restore()

                return 0
            else:
                logger.error(
                    "Backup restoration failed",
                    extra={
                        "operation": "backup_restoration",
                        "backup_id": backup_id,
                        "error": result.get("error", "Unknown error"),
                    },
                )
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
        with logger.operation_context(operation="smart_restore"):
            with logger.profile_context("smart_restore"):
                success = self.restore_manager.smart_restore(
                    include_playlists=include_playlists, include_songs=include_songs
                )

            if success:
                logger.info(
                    "Smart restore completed successfully",
                    extra={
                        "operation": "smart_restore",
                        "include_playlists": include_playlists,
                        "include_songs": include_songs,
                    },
                )
            else:
                logger.error(
                    "Smart restore failed",
                    extra={
                        "operation": "smart_restore",
                        "include_playlists": include_playlists,
                        "include_songs": include_songs,
                    },
                )

            return 0 if success else 1
