"""
Spotify Setup Module

This module provides functionality for setting up Spotify API credentials.
"""

import os
import json
import questionary
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from ...utils.path_manager import PathManager

_path_manager = PathManager()


class SpotifySetup:
    """Class for setting up Spotify API credentials."""

    def __init__(self):
        """Initialize the SpotifySetup."""
        self.console = Console()

        # Create credentials directory if it doesn't exist
        credentials_dir = _path_manager.app_dir / "credentials"
        credentials_dir.mkdir(parents=True, exist_ok=True)

        # Define credentials file path
        self.credentials_file = credentials_dir / "spotify_credentials.json"

    def setup_credentials(self):
        """Set up Spotify API credentials."""
        self.console.print(
            Panel(
                Markdown("""
# Spotify API Credentials Setup

To use Spotify integration features, you need to provide API credentials.

## IMPORTANT NOTE ABOUT REDIRECT URI

You MUST set the Redirect URI in your Spotify app to **exactly**: 
`http://localhost:8080`

## Step-by-Step Instructions

1. Visit [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Log in with your Spotify account
3. Click "CREATE APP" button
4. Fill in:
   - App name: "Aurras Music Player" (or any name)
   - App description: "Music player app"
   - Website: You can leave this blank
   - Redirect URI: `http://localhost:8080` (EXACT match required)
5. Check the agreement checkbox and click "CREATE"
6. On your app page, copy the "Client ID" 
7. Click "SHOW CLIENT SECRET" and copy the secret

If you have issues with authentication later:
- Go back to your app in the Spotify Dashboard
- Click "EDIT SETTINGS"
- Double-check the Redirect URI is EXACTLY: `http://localhost:8080`
            """),
                title="Spotify Setup",
                border_style="green",
                width=100,
            )
        )

        # Check if credentials already exist
        if self.credentials_file.exists():
            overwrite = questionary.confirm(
                "Spotify credentials already exist. Do you want to overwrite them?",
                default=False,
            ).ask()

            if not overwrite:
                self.console.print("[yellow]Setup cancelled.[/yellow]")
                return False

        # Ask for client ID
        client_id = questionary.text("Enter your Spotify Client ID:").ask()
        if not client_id:
            self.console.print("[yellow]Setup cancelled.[/yellow]")
            return False

        # Ask for client secret
        client_secret = questionary.password("Enter your Spotify Client Secret:").ask()
        if not client_secret:
            self.console.print("[yellow]Setup cancelled.[/yellow]")
            return False

        # Save the credentials
        credentials = {"client_id": client_id, "client_secret": client_secret}

        try:
            with open(self.credentials_file, "w") as f:
                json.dump(credentials, f)
            # Set restrictive permissions on the file
            os.chmod(self.credentials_file, 0o600)
            self.console.print("[green]Spotify credentials saved successfully.[/green]")
            self.console.print(
                "[green]You can now use the 'import_playlist' command to import your Spotify playlists.[/green]"
            )
            return True
        except Exception as e:
            self.console.print(f"[bold red]Error saving credentials: {e}[/bold red]")
            return False
