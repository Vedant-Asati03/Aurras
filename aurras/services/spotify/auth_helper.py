"""
Spotify Authentication Helper

This standalone script can help with Spotify authentication when the built-in flow fails.
"""

import os
import json
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

console = Console()


def main():
    """Run the Spotify authentication helper."""
    console.print(
        Panel(
            "This helper will guide you through authenticating with Spotify.\n"
            "It will generate a token that Aurras can use to access your playlists.",
            title="Spotify Authentication Helper",
            border_style="green",
        )
    )

    # Get app directory
    app_dir = Path.home() / ".aurras"
    credentials_dir = app_dir / "credentials"
    credentials_file = credentials_dir / "spotify_credentials.json"

    # Check for credentials file
    if not credentials_file.exists():
        console.print("[bold red]No Spotify credentials found![/bold red]")
        console.print("Please run 'setup_spotify' in Aurras first.")
        return

    # Read credentials
    try:
        with open(credentials_file, "r") as f:
            credentials = json.load(f)
    except Exception as e:
        console.print(f"[bold red]Error reading credentials: {e}[/bold red]")
        return

    # Authenticate
    try:
        redirect_uri = "http://localhost:8080"
        scope = "playlist-read-private"

        console.print("[cyan]Attempting authentication...[/cyan]")
        console.print(f"Client ID: {credentials['client_id'][:5]}...")
        console.print(f"Redirect URI: {redirect_uri}")

        auth = SpotifyOAuth(
            client_id=credentials["client_id"],
            client_secret=credentials["client_secret"],
            redirect_uri=redirect_uri,
            scope=scope,
            open_browser=True,
            cache_path=str(app_dir / ".cache-spotify"),
        )

        token_info = auth.get_access_token()

        if token_info:
            console.print("[bold green]Authentication successful![/bold green]")
            console.print(
                "You can now return to Aurras and use the import_playlist command."
            )
        else:
            console.print("[bold red]Authentication failed.[/bold red]")

    except Exception as e:
        console.print(f"[bold red]Error during authentication: {e}[/bold red]")


if __name__ == "__main__":
    main()
