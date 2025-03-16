import os
import spotipy
from spotipy import util, oauth2
import sqlite3
import questionary
from pathlib import Path
import json
import webbrowser
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.markdown import Markdown
import time

from ...utils.path_manager import PathManager

_path_manager = PathManager()


class ImportSpotifyPlaylist:
    """Class to import playlists from Spotify."""

    def __init__(self):
        """Initialize the Spotify client and authenticate the user."""
        self.console = Console()
        self.scope = "playlist-read-private"
        self.spotify_playlists = None
        self.selected_playlist = None
        self.spotify_client = None
        self.spotify_user_playlists = None
        self.tracks_in_playlist = None
        self.selected_playlist_name = None

        # Ensure database directory exists
        _path_manager.database_dir.mkdir(parents=True, exist_ok=True)

        # Create credentials directory if it doesn't exist
        credentials_dir = _path_manager.app_dir / "credentials"
        credentials_dir.mkdir(parents=True, exist_ok=True)

        # Define credentials file path
        self.credentials_file = credentials_dir / "spotify_credentials.json"

        # Define token cache path
        self.token_cache_path = _path_manager.app_dir / ".cache-spotify"

    def _setup_spotify_client(self):
        """Set up the Spotify client with proper authentication."""
        # Check if we have credentials
        credentials = self._load_credentials()
        if not credentials:
            # No saved credentials, prompt user to enter them
            credentials = self._prompt_for_credentials()
            if not credentials:
                # User cancelled or provided invalid credentials
                raise ValueError("Spotify credentials are required.")

            # Save the credentials for future use
            self._save_credentials(credentials)

        # Define redirect URI - MUST match exactly what's in Spotify Dashboard
        redirect_uri = "http://localhost:8080"

        try:
            # Create the auth manager that will handle token caching
            auth_manager = oauth2.SpotifyOAuth(
                client_id=credentials["client_id"],
                client_secret=credentials["client_secret"],
                redirect_uri=redirect_uri,
                scope=self.scope,
                open_browser=False,
                cache_path=str(self.token_cache_path),
            )

            # First, check if we have a cached token
            token_info = None
            if self.token_cache_path.exists():
                try:
                    token_info = auth_manager.get_cached_token()
                except Exception:
                    # If there's any issue with the cached token, we'll ignore it
                    pass

            # If we have a valid token, use it
            if token_info and not auth_manager.is_token_expired(token_info):
                self.console.print(
                    "[green]Using existing Spotify authorization[/green]"
                )
                token = token_info["access_token"]

            # If token exists but is expired, try to refresh it
            elif (
                token_info
                and auth_manager.is_token_expired(token_info)
                and token_info.get("refresh_token")
            ):
                self.console.print("[cyan]Refreshing Spotify authorization...[/cyan]")
                try:
                    token_info = auth_manager.refresh_access_token(
                        token_info["refresh_token"]
                    )
                    token = token_info["access_token"]
                    self.console.print(
                        "[green]Successfully refreshed authorization[/green]"
                    )
                except Exception as e:
                    self.console.print(
                        f"[yellow]Failed to refresh token: {e}. Will need to re-authenticate.[/yellow]"
                    )
                    # If refresh fails, we'll continue with the full auth flow
                    token_info = None
                    token = None
            else:
                token_info = None
                token = None

            # If we don't have a valid token after trying to use/refresh the cached one,
            # go through the full auth flow
            if not token_info or not token:
                self.console.print(
                    Panel(
                        Markdown("""
# Spotify Authentication

1. A browser window will open to authorize access to your Spotify account.
2. **AFTER you authorize the app**, you'll be redirected to a page that may show an error.
3. **IMPORTANT**: Look at your browser's address bar and copy the ENTIRE URL.
   - The URL should start with `http://localhost:8080?code=...`
   - This is NOT the same as the original Spotify authorization URL
   - If you don't see this URL, check if your Spotify app has the correct redirect URI

⚠️ Copy the URL from your BROWSER ADDRESS BAR AFTER authorization completes, not the initial URL!
                """),
                        title="Spotify Authorization Instructions",
                        border_style="green",
                    )
                )

                # Get the auth URL
                auth_url = auth_manager.get_authorize_url()

                # Open browser with the authorization URL
                self.console.print(
                    "[cyan]Opening browser for Spotify authorization...[/cyan]"
                )

                try:
                    webbrowser.open(auth_url)
                    self.console.print(
                        "[green]Browser opened with authentication URL[/green]"
                    )
                except:
                    self.console.print(
                        "[yellow]Could not open browser automatically.[/yellow]"
                    )
                    self.console.print(f"Please open this URL manually: {auth_url}")

                # Prompt user for the response URL
                self.console.print(
                    "\n[bold yellow]⚠️ IMPORTANT: AFTER authorizing in your browser:[/bold yellow]"
                )
                self.console.print(
                    "[yellow]1. Look at your browser's address bar[/yellow]"
                )
                self.console.print(
                    "[yellow]2. Copy the FULL URL starting with 'http://localhost:8080'[/yellow]"
                )
                self.console.print(
                    "[yellow]3. Paste that URL below (NOT the original Spotify URL)[/yellow]"
                )

                # Manual code entry with validation
                redirect_url = questionary.text(
                    "Enter the COMPLETE redirect URL from your browser (starts with http://localhost:8080):"
                ).ask()

                # Validate the URL format
                if not redirect_url:
                    raise ValueError("Authentication cancelled")

                if redirect_url.startswith("https://accounts.spotify.com"):
                    self.console.print(
                        "\n[bold red]ERROR: You provided the original Spotify authorization URL, not the redirect URL![/bold red]"
                    )
                    self.console.print(
                        "[yellow]The correct URL should start with 'http://localhost:8080' and appear in your browser AFTER authorization.[/yellow]"
                    )
                    raise ValueError(
                        "Incorrect URL provided - need redirect URL, not original authorization URL"
                    )

                if not redirect_url.startswith("http://localhost:8080"):
                    self.console.print(
                        "\n[bold red]ERROR: The URL you provided doesn't start with 'http://localhost:8080'[/bold red]"
                    )
                    self.console.print(
                        "[yellow]Please check that you're copying the correct URL from your browser after authorization.[/yellow]"
                    )
                    raise ValueError("Invalid redirect URL format")

                # Extract the code and get the token
                try:
                    code = auth_manager.parse_response_code(redirect_url)
                    token_info = auth_manager.get_access_token(code)
                    token = token_info["access_token"]
                    self.console.print(
                        "[green]Authorization successful! Token saved for future use.[/green]"
                    )
                except Exception as e:
                    if "invalid_grant" in str(e).lower():
                        self.console.print(
                            "\n[bold red]Authentication Error: Invalid authorization code[/bold red]"
                        )
                        self.console.print(
                            "[yellow]This usually happens when:[/yellow]"
                        )
                        self.console.print(
                            "  [yellow]1. The code has expired (waited too long)[/yellow]"
                        )
                        self.console.print(
                            "  [yellow]2. You provided the wrong URL[/yellow]"
                        )
                        self.console.print(
                            "  [yellow]3. The redirect URI in your Spotify app doesn't match exactly[/yellow]"
                        )

                        # Offer to try again
                        retry = questionary.confirm(
                            "Would you like to try again?", default=True
                        ).ask()
                        if retry:
                            # Recursive call to try again
                            return self._setup_spotify_client()
                    raise

            # Create the Spotify client with the token
            self.spotify_client = spotipy.Spotify(auth=token)

            # Test the connection
            user = self.spotify_client.current_user()
            self.console.print(
                f"[green]Connected to Spotify as: {user['display_name']}![/green]"
            )

        except Exception as e:
            self._handle_auth_error(e)
            raise

    def _handle_auth_error(self, e):
        """Handle Spotify authentication errors with helpful messages."""
        self.console.print(f"[bold red]Error connecting to Spotify: {e}[/bold red]")

        # Handle specific error conditions with helpful messages
        error_message = str(e).lower()
        if "invalid_client" in error_message and "redirect" in error_message:
            self.console.print(
                Panel(
                    """
[bold red]INVALID REDIRECT URI ERROR[/bold red]

This error occurs when the redirect URI in your Spotify app settings doesn't exactly match "http://localhost:8080".

To fix this:
1. Go to your [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/applications)
2. Select your app
3. Click "EDIT SETTINGS"
4. Under "Redirect URIs", make sure you have EXACTLY: http://localhost:8080
   - No trailing slash
   - No extra spaces
   - Correct capitalization (all lowercase)
5. Click "SAVE" at the bottom
6. Try importing again
                """,
                    title="Redirect URI Configuration Error",
                    border_style="red",
                    width=100,
                )
            )
        elif "invalid_grant" in error_message:
            self.console.print(
                "[yellow]Authentication timeout - the code has expired. Please try again.[/yellow]"
            )
        elif "invalid_client" in error_message:
            self.console.print(
                "[yellow]Invalid Client ID or Client Secret. Please check your credentials.[/yellow]"
            )
            if self.credentials_file.exists():
                self.credentials_file.unlink()

    def _prompt_for_credentials(self):
        """Prompt the user for Spotify API credentials."""
        self.console.print(
            Panel(
                "[bold cyan]Spotify API Credentials Required[/bold cyan]\n\n"
                "To import playlists from Spotify, you need to provide API credentials.\n"
                "Visit [link=https://developer.spotify.com/dashboard/applications]https://developer.spotify.com/dashboard/applications[/link]\n"
                "1. Log in with your Spotify account\n"
                "2. Create a new application\n"
                "3. Add 'http://localhost:8080' as a Redirect URI in the app settings\n"
                "4. Copy the Client ID and Client Secret\n",
                title="Spotify Setup",
                border_style="green",
            )
        )

        # Ask for client ID
        client_id = questionary.text("Enter your Spotify Client ID:").ask()
        if not client_id:
            self.console.print("[yellow]Setup cancelled.[/yellow]")
            return None

        # Ask for client secret
        client_secret = questionary.password("Enter your Spotify Client Secret:").ask()
        if not client_secret:
            self.console.print("[yellow]Setup cancelled.[/yellow]")
            return None

        return {"client_id": client_id, "client_secret": client_secret}

    def _save_credentials(self, credentials):
        """Save Spotify credentials to file."""
        try:
            with open(self.credentials_file, "w") as f:
                json.dump(credentials, f)
            # Set restrictive permissions on the file
            os.chmod(self.credentials_file, 0o600)
            self.console.print("[green]Credentials saved successfully.[/green]")
        except Exception as e:
            self.console.print(f"[bold red]Error saving credentials: {e}[/bold red]")

    def _load_credentials(self):
        """Load Spotify credentials from file."""
        if not self.credentials_file.exists():
            return None

        try:
            with open(self.credentials_file, "r") as f:
                return json.load(f)
        except Exception:
            # If there's any error reading the file, return None
            return None

    def _fetch_user_playlists(self):
        """Fetch user's playlists from Spotify."""
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold green]Fetching playlists...[/bold green]"),
                console=self.console,
                transient=True,
            ) as progress:
                progress.add_task("Fetching", total=None)
                self.spotify_user_playlists = (
                    self.spotify_client.current_user_playlists(limit=50)
                )

                # Fix: Check if we actually got playlists
                if (
                    not self.spotify_user_playlists
                    or not self.spotify_user_playlists.get("items")
                ):
                    self.console.print(
                        "[bold red]No playlists found in your Spotify account.[/bold red]"
                    )
                    return False
                return True
        except Exception as e:
            self.console.print(f"[bold red]Error fetching playlists: {e}[/bold red]")
            return False

    def _select_playlist_to_import(self):
        """Let the user select a playlist to import."""
        playlist_choices = []
        for item in self.spotify_user_playlists["items"]:
            playlist_choices.append(item["name"])

        self.selected_playlist = questionary.select(
            "Select a playlist to import:", choices=playlist_choices
        ).ask()

        if not self.selected_playlist:
            self.console.print("[yellow]Playlist selection cancelled.[/yellow]")
            return False
        return True

    def _track_spotify_playlist(self):
        """Track the songs in the selected Spotify playlist."""
        try:
            # Find the selected playlist ID
            playlist_id = None
            for item in self.spotify_user_playlists["items"]:
                if item["name"] == self.selected_playlist:
                    playlist_id = item["id"]
                    break

            if not playlist_id:
                self.console.print(
                    f"[bold red]Couldn't find playlist ID for '{self.selected_playlist}'[/bold red]"
                )
                return False

            # Get the tracks from the playlist
            with Progress(
                SpinnerColumn(),
                TextColumn(
                    f"[bold green]Fetching songs from {self.selected_playlist}...[/bold green]"
                ),
                console=self.console,
                transient=True,
            ) as progress:
                progress.add_task("Fetching", total=None)
                results = self.spotify_client.playlist_tracks(playlist_id=playlist_id)

            tracks = []
            for item in results["items"]:
                if item["track"]:
                    track_name = item["track"]["name"]
                    artist_name = item["track"]["artists"][0]["name"]
                    tracks.append(f"{track_name} - {artist_name}")

            self.tracks_in_playlist = tracks
            self.selected_playlist_name = self.selected_playlist
            return bool(tracks)
        except Exception as e:
            self.console.print(f"[bold red]Error tracking playlist: {e}[/bold red]")
            return False

    def _save_playlist_to_db(self):
        """Save the imported playlist to the local database."""
        if not self.tracks_in_playlist:
            self.console.print("[bold red]No tracks to save.[/bold red]")
            return False

        try:
            # Create database directory if not exists
            _path_manager.database_dir.mkdir(parents=True, exist_ok=True)

            # Sanitize playlist name for database use (replace spaces with underscores)
            safe_playlist_name = self.selected_playlist_name.lower().replace(" ", "_")

            with sqlite3.connect(_path_manager.saved_playlists) as playlists:
                cursor = playlists.cursor()

                # Check if playlist already exists
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (safe_playlist_name,),
                )
                if cursor.fetchone():
                    # Ask if the user wants to overwrite
                    overwrite = questionary.confirm(
                        f"Playlist '{self.selected_playlist_name}' already exists. Overwrite?",
                        default=False,
                    ).ask()

                    if not overwrite:
                        self.console.print("[yellow]Import cancelled.[/yellow]")
                        return False

                    # Drop the existing table
                    cursor.execute(f"DROP TABLE IF EXISTS '{safe_playlist_name}'")

                # Create the playlist table
                cursor.execute(
                    f"CREATE TABLE '{safe_playlist_name}' (id INTEGER PRIMARY KEY, playlists_songs TEXT)"
                )

                # Insert all tracks
                for track in self.tracks_in_playlist:
                    cursor.execute(
                        f"INSERT INTO '{safe_playlist_name}' (playlists_songs) VALUES (?)",
                        (track,),
                    )

                playlists.commit()

                self.console.print(
                    f"[green]Successfully imported {len(self.tracks_in_playlist)} songs to playlist '{self.selected_playlist_name}'[/green]"
                )
                return True
        except Exception as e:
            self.console.print(f"[bold red]Error saving playlist: {e}[/bold red]")
            return False

    def import_spotify_playlist(self):
        """Import a playlist from Spotify."""
        try:
            # Set up the Spotify client
            self._setup_spotify_client()

            if not self._fetch_user_playlists():
                return False

            if not self._select_playlist_to_import():
                return False

            if not self._track_spotify_playlist():
                return False

            return self._save_playlist_to_db()
        except ValueError as e:
            # This is for user cancellation or other expected errors
            self.console.print(f"[yellow]{str(e)}[/yellow]")
            return False
        except Exception as e:
            # Handle unexpected errors
            self.console.print(
                f"[bold red]Error importing playlist: {str(e)}[/bold red]"
            )
            return False
