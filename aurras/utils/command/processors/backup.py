"""
Backup processor for Aurras CLI.

This module handles backup-related commands and operations such as
creating, restoring, and managing backups of user data.
"""

from typing import Optional
from datetime import datetime

from aurras.utils.console import console
from aurras.utils.logger import get_logger
from aurras.utils.backup_manager import BackupManager
from aurras.utils.decorators import with_error_handling

logger = get_logger("aurras.command.processors.backup", log_to_console=False)


class BackupProcessor:
    """Handle backup-related commands and operations."""

    def __init__(self):
        """Initialize the backup processor."""
        self.backup_manager = BackupManager()

    @with_error_handling
    def create_backup(self, backup_name: Optional[str] = None) -> int:
        """
        Create a new backup of user data.

        Args:
            backup_name: Optional name for the backup

        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        try:
            # Generate a default name if none provided
            if not backup_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"backup_{timestamp}"
                logger.debug(f"Generated default backup name: {backup_name}")
            else:
                logger.info(f"Using provided backup name: {backup_name}")

            logger.info(f"Starting backup creation process with name: {backup_name}")

            # Create a progress display using themed console
            progress = console.create_progress()

            with progress:
                task = progress.add_task("Creating backup...", total=100)

                # Update progress callback
                def update_progress(percent: int):
                    logger.debug(f"Backup progress: {percent}%")
                    progress.update(task, completed=percent)

                # Create the backup
                logger.debug("Calling backup_manager.create_backup()")
                backup_path = self.backup_manager.create_backup(
                    backup_name, progress_callback=update_progress
                )

            if not backup_path:
                logger.error("Backup creation failed - empty backup path returned")
                console.print_error("Failed to create backup")
                return 1

            # Show success message in a panel
            logger.info(f"Backup successfully created at: {backup_path}")
            panel = console.create_panel(
                f"Backup saved to: {backup_path}",
                title="Backup Created Successfully",
                style="success",
            )
            console.print(panel)
            return 0

        except Exception as e:
            logger.exception(f"Error creating backup: {e}")
            console.print_error(f"Error creating backup: {e}")
            return 1

    @with_error_handling
    def list_backups(self) -> int:
        """
        List all available backups.

        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        logger.info("Retrieving list of available backups")
        try:
            logger.debug("Calling backup_manager.get_available_backups()")
            backups = self.backup_manager.get_available_backups()

            if not backups:
                logger.info("No backups found in the backup directory")
                console.print_info("No backups found")
                return 0

            logger.info(f"Found {len(backups)} available backups")

            # Create a table to display backups
            table = console.create_table(
                title="Available Backups", caption=f"Total: {len(backups)} backup(s)"
            )

            table.add_column("Name")
            table.add_column("Created")
            table.add_column("Size")
            table.add_column("Type")

            total_size = 0
            oldest_timestamp = float("inf")
            newest_timestamp = 0

            for backup in backups:
                # Track statistics for logging
                total_size += backup["size"]
                oldest_timestamp = min(oldest_timestamp, backup["timestamp"])
                newest_timestamp = max(newest_timestamp, backup["timestamp"])

                # Format timestamp
                created = datetime.fromtimestamp(backup["timestamp"]).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

                # Format size
                size = backup["size"]
                if size < 1024:
                    size_str = f"{size} B"
                elif size < 1024 * 1024:
                    size_str = f"{size / 1024:.1f} KB"
                else:
                    size_str = f"{size / (1024 * 1024):.1f} MB"

                table.add_row(backup["name"], created, size_str, backup["type"])

            # Log backup statistics
            total_mb = total_size / (1024 * 1024)
            oldest_date = datetime.fromtimestamp(oldest_timestamp).strftime("%Y-%m-%d")
            newest_date = datetime.fromtimestamp(newest_timestamp).strftime("%Y-%m-%d")
            logger.info(
                f"Backup statistics: {len(backups)} backups, {total_mb:.2f} MB total, date range: {oldest_date} to {newest_date}"
            )

            console.print(table)
            return 0

        except Exception as e:
            logger.exception(f"Error listing backups: {e}")
            console.print_error(f"Error listing backups: {e}")
            return 1

    @with_error_handling
    def restore_backup(self, backup_name: str) -> int:
        """
        Restore a backup.

        Args:
            backup_name: Name of the backup to restore

        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        if not backup_name:
            console.print_error("Backup name cannot be empty")
            return 1

        try:
            # Check if backup exists
            backups = self.backup_manager.get_available_backups()
            backup = next((b for b in backups if b["name"] == backup_name), None)

            if not backup:
                console.print_error(f"Backup '{backup_name}' not found")
                self.list_backups()  # Show available backups
                return 1

            # Get confirmation with themed prompt
            confirm = console.confirm(
                f"Are you sure you want to restore backup '{backup_name}'? "
                f"This will overwrite your current data.",
                style_key="warning",
            )

            if not confirm:
                console.print_info("Restore operation cancelled")
                return 0

            # Create a progress bar for restore operation
            progress = console.create_progress(
                description_style="bold red",  # Use red to indicate caution
                completed_style="red",
            )

            with progress:
                task = progress.add_task("Restoring backup...", total=100)

                # Update progress callback
                def update_progress(percent: int):
                    progress.update(task, completed=percent)

                # Restore the backup
                success = self.backup_manager.restore_backup(
                    backup_name, progress_callback=update_progress
                )

            if not success:
                console.print_error(f"Failed to restore backup '{backup_name}'")
                return 1

            # Show success message in a panel
            panel = console.create_panel(
                "Your data has been restored to the selected backup state.\n"
                "You may need to restart the application for all changes to take effect.",
                title="Backup Restored Successfully",
                style="success",
            )
            console.print(panel)
            return 0

        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            console.print_error(f"Error restoring backup: {e}")
            return 1

    @with_error_handling
    def delete_backup(self, backup_name: str) -> int:
        """
        Delete a backup.

        Args:
            backup_name: Name of the backup to delete

        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        if not backup_name:
            console.print_error("Backup name cannot be empty")
            return 1

        try:
            # Check if backup exists
            backups = self.backup_manager.get_available_backups()
            backup = next((b for b in backups if b["name"] == backup_name), None)

            if not backup:
                console.print_error(f"Backup '{backup_name}' not found")
                self.list_backups()  # Show available backups
                return 1

            # Get confirmation
            confirm = console.confirm(
                f"Are you sure you want to delete backup '{backup_name}'? "
                f"This cannot be undone.",
                style_key="error",  # Use error style for destructive action
            )

            if not confirm:
                console.print_info("Delete operation cancelled")
                return 0

            # Show status while deleting
            with console.status(
                console.style_text(f"Deleting backup '{backup_name}'...", "warning"),
                spinner="dots",
            ):
                success = self.backup_manager.delete_backup(backup_name)

            if not success:
                console.print_error(f"Failed to delete backup '{backup_name}'")
                return 1

            console.print_success(f"Backup '{backup_name}' deleted successfully")
            return 0

        except Exception as e:
            logger.error(f"Error deleting backup: {e}")
            console.print_error(f"Error deleting backup: {e}")
            return 1
