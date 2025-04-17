"""
Backup command processor for Aurras CLI.

This module handles backup and restore operations for settings and data.
"""

import logging
from rich.table import Table
from rich.box import ROUNDED

from ...backup_manager import BackupManager
from ...console import get_console

# Get logger
logger = logging.getLogger(__name__)

# Get rich console for output
console = get_console()


class BackupProcessor:
    """Handle backup and restore operations."""

    def __init__(self):
        """Initialize the backup processor."""
        self.backup_manager = BackupManager()

    def create_backup(self):
        """Create a manual backup of user settings and data."""
        result = self.backup_manager.create_backup(manual=True)
        if result:
            console.print("[green]Backup created successfully[/green]")
        else:
            console.print("[yellow]Failed to create backup[/yellow]")
        return 0 if result else 1

    def list_backups(self):
        """List all available backups with their details."""
        backups = self.backup_manager.list_available_backups()

        if not backups:
            console.print("[yellow]No backups found[/yellow]")
            return 0

        table = Table(title="Available Backups", box=ROUNDED, border_style="cyan")
        table.add_column("#", style="dim")
        table.add_column("Date", style="green")
        table.add_column("Type", style="cyan")
        table.add_column("Content", style="cyan")
        table.add_column("Size", style="cyan")

        for i, backup in enumerate(backups, 1):
            table.add_row(
                str(i),
                backup.get("date", "Unknown"),
                "Manual" if backup.get("manual", False) else "Auto",
                ", ".join(backup.get("items", {}).keys()),
                backup.get("size", "Unknown"),
            )

        console.print(table)
        return 0

    def restore_backup(self, backup_id=None):
        """Restore from a specified backup or prompt user to select one."""
        backups = self.backup_manager.list_available_backups()

        if not backups:
            console.print("[yellow]No backups found[/yellow]")
            return 1

        if backup_id is None:
            # Display backups and ask which one to restore
            self.list_backups()
            backup_id = console.input("[cyan]Enter backup number to restore: [/cyan]")

        try:
            index = int(backup_id) - 1
            if 0 <= index < len(backups):
                # Confirm restoration
                confirm = console.input(
                    "[yellow]This will overwrite your current settings and data. Continue? (y/n): [/yellow]"
                )

                if confirm.lower() == "y":
                    backup_file = backups[index]["file"]
                    result = self.backup_manager.restore_from_backup(backup_file)
                    if result:
                        console.print("[green]Backup restored successfully[/green]")
                        return 0
                    else:
                        console.print("[red]Failed to restore backup[/red]")
                        return 1
                else:
                    console.print("[yellow]Restoration cancelled[/yellow]")
                    return 0
            else:
                console.print("[red]Invalid backup number[/red]")
                return 1
        except ValueError:
            console.print("[red]Invalid input. Please enter a number.[/red]")
            return 1


# Instantiate processor for direct import
processor = BackupProcessor()
