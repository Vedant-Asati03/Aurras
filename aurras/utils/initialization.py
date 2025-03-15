"""
Initialization Module

This module handles initialization tasks when Aurras starts up.
"""

from rich.console import Console
from ..utils.backup_manager import BackupManager
from ..core.settings import LoadDefaultSettings

console = Console()


def initialize_application():
    """
    Perform initialization tasks when the application starts.

    This includes checking for backup needs and other startup tasks.
    """
    settings = LoadDefaultSettings().load_default_settings()

    # Check if backup is enabled and due
    if settings.get("backup", {}).get("enabled", "yes").lower() == "yes":
        try:
            backup_manager = BackupManager()
            backup_manager.check_and_backup()
        except Exception as e:
            console.print(f"[yellow]Backup check failed: {e}[/yellow]")

    # Add other initialization tasks here as needed

    return True
