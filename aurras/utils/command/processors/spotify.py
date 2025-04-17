"""
Spotify service processor for Aurras CLI.

This module handles Spotify-related commands and operations such as
authentication, playlist importing, and service configuration.
"""

import time
import signal
import logging
import questionary
from typing import Optional
from pathlib import Path

from rich.panel import Panel
from rich.console import Console

from ....services.spotify.setup import SpotifySetup
from ....services.spotify.importer import ImportSpotifyPlaylist
from ...path_manager import PathManager
from ...theme_helper import ThemeHelper, with_error_handling

logger = logging.getLogger(__name__)
console = Console()
path_manager = PathManager()


class SpotifyProcessor:
    """Handle Spotify-related commands and operations."""

    def __init__(self):
        """Initialize the Spotify processor."""
        pass

    @with_error_handling
    def setup_spotify(self) -> int:
        """
        Set up Spotify API credentials.

        This guides the user through setting up Spotify API credentials
        for integration with Aurras.

        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        try:
            spotify_setup = SpotifySetup()
            if spotify_setup.setup_credentials():
                console.print("[green]Spotify setup completed successfully.[/green]")
                console.print(
                    "You can now use [bold]import_playlist[/bold] to import your Spotify playlists."
                )
                return 0
            else:
                console.print("[yellow]Spotify setup was not completed.[/yellow]")
                return 1
        except Exception as e:
            console.print(f"[bold red]Error during Spotify setup:[/bold red] {str(e)}")
            return 1

    @with_error_handling
    def import_playlist(self, playlist_name: Optional[str] = None) -> int:
        """
        Import playlists from Spotify.

        This method connects to Spotify and imports playlists for use in Aurras.

        Args:
            playlist_name: Optional name of playlist to import. If None, imports all playlists.

        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        try:
            credentials_file = (
                path_manager.app_dir / "credentials" / "spotify_credentials.json"
            )

            # Check if credentials exist
            if not credentials_file.exists():
                console.print("[yellow]Spotify credentials not found.[/yellow]")
                setup_now = questionary.confirm(
                    "Would you like to set up Spotify now?", default=True
                ).ask()

                if setup_now:
                    if self.setup_spotify() != 0:
                        return 1
                else:
                    console.print(
                        "[yellow]Spotify setup is required to import playlists.[/yellow]"
                    )
                    console.print(
                        "Use the [bold]setup_spotify[/bold] command to set up."
                    )
                    return 1

            # Show warning about potential issues
            console.print(
                Panel(
                    """
[bold cyan]Before connecting to Spotify:[/bold cyan]

If you experience authentication issues (like "Invalid redirect URI"):
1. Double-check that your Spotify app's Redirect URI is EXACTLY: http://localhost:8080
2. Make sure your Client ID and Secret are correct

The next step will connect to Spotify. If you get stuck or see errors, you can:
1. Press Ctrl+C to cancel
2. Run 'setup_spotify' again with updated settings
                """,
                    title="Important Spotify Connection Info",
                    border_style="yellow",
                )
            )

            proceed = questionary.confirm(
                "Ready to connect to Spotify?", default=True
            ).ask()

            if not proceed:
                console.print("[yellow]Import cancelled.[/yellow]")
                return 1

            # Create the importer instance
            importer = ImportSpotifyPlaylist()

            # Set a reasonable timeout for the operation
            def timeout_handler(signum, frame):
                raise TimeoutError("Spotify connection timed out")

            # Set 60 second timeout
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(60)

            try:
                console.print("[cyan]Connecting to Spotify...[/cyan]")
                importer.import_spotify_playlist(playlist_name=playlist_name)
                # Turn off the alarm
                signal.alarm(0)
                return 0
            except TimeoutError:
                console.print("[bold red]Connection to Spotify timed out.[/bold red]")
                console.print("This usually happens due to authentication issues.")

                # Offer alternative
                help_path = (
                    path_manager.app_dir / "services" / "spotify" / "auth_helper.py"
                )
                console.print(
                    f"Try running the standalone auth helper: [cyan]python {help_path}[/cyan]"
                )
                return 1
            except KeyboardInterrupt:
                # Turn off the alarm
                signal.alarm(0)
                console.print("\n[yellow]Operation cancelled by user.[/yellow]")
                return 1

        except ValueError as e:
            console.print(f"[yellow]{str(e)}[/yellow]")
            return 1
        except Exception as e:
            console.print(f"[bold red]Error importing playlist:[/bold red] {str(e)}")
            return 1


# Instantiate processor for direct import
processor = SpotifyProcessor()
