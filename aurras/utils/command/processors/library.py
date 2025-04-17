"""
Library command processor for Aurras CLI.

This module handles library management commands and operations.
"""

import os
import logging

from ....core.settings import load_settings, SettingsUpdater
from ...console.manager import get_console

# Get logger
logger = logging.getLogger(__name__)

# Get rich console for output
console = get_console()


class LibraryProcessor:
    """Handle library management operations."""

    def __init__(self):
        """Initialize the library processor."""
        self.settings = load_settings()

    def scan_library(self):
        """Scan the music library for new files."""
        console.print("[cyan]Scanning music library...[/cyan]")

        # Get the library path from settings
        library_path = self.settings.get("library_path", "~/Music")
        expanded_path = os.path.expanduser(library_path)

        if not os.path.exists(expanded_path):
            console.print(f"[yellow]Library path not found: {expanded_path}[/yellow]")
            return 1

        # Count files in directory (this is just a placeholder - a real scanner would do more)
        file_count = 0
        for root, _, files in os.walk(expanded_path):
            for file in files:
                if file.endswith((".mp3", ".flac", ".wav", ".ogg", ".m4a")):
                    file_count += 1

        console.print(
            f"[green]Library scan complete! Found {file_count} music files.[/green]"
        )
        return 0

    def list_playlists(self):
        """List all playlists in the library."""
        # This would be implemented to list available playlists from the library
        console.print("[yellow]Feature not yet implemented: listing playlists[/yellow]")
        return 0

    def set_library_path(self, path):
        """Set the library path to the provided directory."""
        try:
            expanded_path = os.path.expanduser(path)

            # Check if path exists
            if not os.path.exists(expanded_path):
                create_dir = console.input(
                    f"[yellow]Path '{expanded_path}' does not exist. Create it? (y/n): [/yellow]"
                )
                if create_dir.lower() == "y":
                    os.makedirs(expanded_path, exist_ok=True)
                else:
                    console.print("[yellow]Operation cancelled[/yellow]")
                    return 1

            # Update the setting
            settings_updater = SettingsUpdater("library-path")
            settings_updater.update_specified_setting_directly(expanded_path)
            console.print(f"[green]Library path set to: {expanded_path}[/green]")
            return 0
        except Exception as e:
            console.print(f"[red]Error setting library path:[/red] {str(e)}")
            return 1

    def count_library(self):
        """Count the number of songs in the library."""
        library_path = self.settings.get("library_path", "~/Music")
        expanded_path = os.path.expanduser(library_path)

        if not os.path.exists(expanded_path):
            console.print(f"[yellow]Library path not found: {expanded_path}[/yellow]")
            return 1

        # Count files
        file_count = 0
        for root, _, files in os.walk(expanded_path):
            for file in files:
                if file.endswith((".mp3", ".flac", ".wav", ".ogg", ".m4a")):
                    file_count += 1

        console.print(f"[green]Your library contains {file_count} music files[/green]")
        return 0


# Instantiate processor for direct import
processor = LibraryProcessor()
