from rich.text import Text
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.box import ROUNDED
import questionary

from ..core.downloader import SongDownloader
from ..playlist.delete import DeletePlaylist
from ..playlist.download import DownloadPlaylist
from ..player.online import ListenSongOnline, ListenPlaylistOnline, play_song_sequence
from ..player.offline import ListenSongOffline, ListenPlaylistOffline
from ..services.spotify.importer import ImportSpotifyPlaylist
from ..player.queue import QueueManager
from ..player.history import RecentlyPlayedManager
from ..core.settings import (
    LoadDefaultSettings,
    UpdateSpecifiedSettings,
)
from ..utils.cache_cleanup import cleanup_lyrics_cache, cleanup_all_caches
from ..playlist.manager import Select
from ..services.spotify.setup import SpotifySetup
from ..utils.path_manager import PathManager  # Add this import

import sqlite3
import time

# Create a single console for consistent styling
console = Console()
_path_manager = PathManager()  # Add this instantiation


class InputCases:
    def __init__(self) -> None:
        self.console = console
        self.queue_manager = QueueManager()

    def display_help(self):
        """Display help information about available commands."""
        help_table = Table(
            show_header=False,
            box=ROUNDED,
            border_style="bright_blue",
            title="♪♫ AURRAS MUSIC PLAYER HELP ♫♪",
            caption="Press Ctrl+C to exit any time",
        )

        help_table.add_column("Section", style="bold cyan")
        help_table.add_column("Description", style="green")

        # Basic usage section
        help_table.add_row("[bold cyan]BASIC USAGE[/bold cyan]", "")
        help_table.add_row("  Type a song name", "Search and play a song")
        help_table.add_row(
            "  Type multiple songs with commas", "Play songs in sequence"
        )
        help_table.add_row("  Use '?' for feature suggestions", "Get command help")
        help_table.add_row("  Press Ctrl+C to exit", "Exit the application")

        # Queue commands
        help_table.add_row("", "")
        help_table.add_row("[bold cyan]QUEUE COMMANDS[/bold cyan]", "")
        help_table.add_row("  queue", "Display the current song queue")
        help_table.add_row("  add_to_queue", "Add a song to the current queue")
        help_table.add_row("  clear_queue", "Clear the current song queue")
        help_table.add_row("  song1, song2, ...", "Play multiple songs in sequence")

        # History commands
        help_table.add_row("", "")
        help_table.add_row("[bold cyan]HISTORY COMMANDS[/bold cyan]", "")
        help_table.add_row("  history", "Show recently played songs")
        help_table.add_row("  previous", "Play the previous song from history")
        help_table.add_row("  clear_history", "Clear your song history")

        # Command shortcuts
        help_table.add_row("", "")
        help_table.add_row("[bold cyan]COMMAND SHORTCUTS[/bold cyan]", "")
        help_table.add_row(
            "  > ", "Open command palette (type '>' and space for quick access)"
        )
        help_table.add_row("  cmd", "Open command palette")
        help_table.add_row("  d, song1, song2, ...", "Download multiple songs")
        help_table.add_row("  dp, playlist_name", "Download a specific playlist")
        help_table.add_row("  pn, playlist_name", "Play a saved playlist online")
        help_table.add_row("  pf, playlist_name", "Play a downloaded playlist offline")
        help_table.add_row("  rs, playlist_name", "Remove a saved playlist")
        help_table.add_row("  rd, playlist_name", "Remove a downloaded playlist")

        # Playlist commands
        help_table.add_row("", "")
        help_table.add_row("[bold cyan]PLAYLIST COMMANDS[/bold cyan]", "")
        help_table.add_row("  play_playlist", "Play songs from a playlist")
        help_table.add_row("  shuffle_playlist", "Play a playlist in random order")
        help_table.add_row("  view_playlist", "View the contents of a playlist")
        help_table.add_row(
            "  add_song_to_playlist", "Add a song to an existing playlist"
        )
        help_table.add_row(
            "  remove_song_from_playlist", "Remove a song from a playlist"
        )
        help_table.add_row("  move_song_up", "Move a song up in the playlist order")
        help_table.add_row("  move_song_down", "Move a song down in the playlist order")
        help_table.add_row("  download_playlist", "Download a playlist for offline use")
        help_table.add_row("  delete_playlist", "Delete a playlist")
        help_table.add_row("  import_playlist", "Import playlists from Spotify")

        # Offline features
        help_table.add_row("", "")
        help_table.add_row("[bold cyan]OFFLINE FEATURES[/bold cyan]", "")
        help_table.add_row("  play_offline", "Browse and play downloaded songs")
        help_table.add_row("  download_song", "Download songs for offline listening")

        # Settings & cache
        help_table.add_row("", "")
        help_table.add_row("[bold cyan]SETTINGS & CACHE[/bold cyan]", "")
        help_table.add_row("  toggle_lyrics", "Turn lyrics display on/off")
        help_table.add_row("  cache_info", "Show information about cached data")
        help_table.add_row("  cleanup_cache", "Delete old cached data")
        help_table.add_row("  cleanup_cache 7", "Delete cache older than 7 days")

        # Playback controls
        help_table.add_row("", "")
        help_table.add_row("[bold cyan]PLAYBACK CONTROLS[/bold cyan]", "")
        help_table.add_row("  q", "End current song playback")
        help_table.add_row("  b", "Play previous song from history")
        help_table.add_row("  n", "Skip to next song")
        help_table.add_row("  p", "Pause/Resume playback")
        help_table.add_row("  t", "Translate lyrics")
        help_table.add_row("  UP/DOWN", "Adjust volume")
        help_table.add_row("  Mouse wheel", "Fine tune volume")

        console.print(help_table)

    def play_offline(self):
        """Browse and play downloaded songs."""
        try:
            with console.status("[cyan]Loading offline songs...[/cyan]"):
                player = ListenSongOffline()
            player.listen_song_offline()
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")

    def download_song(self, songs_to_download=None):
        """Download one or more songs."""
        if songs_to_download is None or songs_to_download == []:
            songs_input = self.console.input(
                Text(
                    "Enter song name[s] (separate multiple songs with commas): ",
                    style="bold cyan",
                )
            )
            # Split by comma and strip whitespace
            songs_to_download = [s.strip() for s in songs_input.split(",") if s.strip()]
            if not songs_to_download:
                self.console.print("[yellow]No valid song names provided.[/yellow]")
                return

        # Create a nice panel to show download list
        songs_list = "\n".join(
            [f"[cyan]{i}.[/cyan] {song}" for i, song in enumerate(songs_to_download, 1)]
        )
        console.print(
            Panel(
                songs_list,
                title=f"Downloading {len(songs_to_download)} Songs",
                border_style="green",
            )
        )

        # Download the songs
        download = SongDownloader(songs_to_download)
        download.download_song()

    def play_playlist(self, online_offline=None, playlist_name=None, shuffle=False):
        """Play songs from a playlist.

        Args:
            online_offline (str, optional): 'n' for online, 'f' for offline
            playlist_name (str, optional): Name of the playlist to play
            shuffle (bool, optional): Whether to shuffle the playlist
        """
        try:
            listen_playlist_online = ListenPlaylistOnline()
            listen_playlist_offline = ListenPlaylistOffline()

            if online_offline is None:
                online_offline = questionary.select(
                    "Select playback mode", choices=["Play Online", "Play Offline"]
                ).ask()

                if not online_offline:  # User cancelled selection
                    console.print("[yellow]Playback cancelled.[/yellow]")
                    return

                online_offline = "n" if online_offline == "Play Online" else "f"

            with console.status("[cyan]Loading playlist...[/cyan]"):
                # Check if playlist exists first
                if playlist_name:
                    if online_offline == "n":
                        # Check if it exists in saved playlists
                        playlist_manager = Select()
                        available_playlists = playlist_manager.load_playlist_from_db()
                        if not available_playlists or playlist_name.lower() not in [
                            p.lower() for p in available_playlists
                        ]:
                            console.print(
                                f"[bold red]Playlist '{playlist_name}' not found in saved playlists.[/bold red]"
                            )
                            return
                    else:  # offline mode
                        # Check if it exists in downloaded playlists
                        available_playlists = _path_manager.list_directory(
                            _path_manager.playlists_dir
                        )
                        if not available_playlists or playlist_name.lower() not in [
                            p.lower() for p in available_playlists
                        ]:
                            console.print(
                                f"[bold red]Playlist '{playlist_name}' not found in downloaded playlists.[/bold red]"
                            )
                            return

                # Play the playlist
                match online_offline:
                    case "n":
                        listen_playlist_online.listen_playlist_online(
                            playlist_name, shuffle=shuffle
                        )
                    case "f":
                        listen_playlist_offline.listen_playlist_offline(
                            playlist_name, shuffle=shuffle
                        )
        except Exception as e:
            console.print(f"[bold red]Error playing playlist: {str(e)}[/bold red]")
            import traceback

            console.print(traceback.format_exc())

    def shuffle_playlist(self, online_offline=None, playlist_name=None):
        """Play a playlist in shuffle mode."""
        self.play_playlist(online_offline, playlist_name, shuffle=True)

    def view_playlist(self, playlist_name=None):
        """View the contents of a playlist."""
        try:
            playlist_manager = Select()
            playlist_manager.display_playlist_contents(playlist_name)
        except Exception as e:
            console.print(f"[bold red]Error viewing playlist:[/bold red] {str(e)}")

    def add_song_to_playlist(self, playlist_name=None, song_name=None):
        """Add a song to an existing playlist."""
        try:
            playlist_manager = Select()

            if playlist_name is None:
                playlist_manager.select_playlist_from_db()
                playlist_name = playlist_manager.active_playlist

            if song_name is None:
                song_name = self.console.input(
                    Text("Enter the name of the song to add: ", style="bold cyan")
                )

            if not song_name.strip():
                self.console.print("[yellow]No song name provided.[/yellow]")
                return

            playlist_manager.add_song_to_playlist(playlist_name, song_name)
        except Exception as e:
            console.print(
                f"[bold red]Error adding song to playlist:[/bold red] {str(e)}"
            )

    def remove_song_from_playlist(self, playlist_name=None, song_name=None):
        """Remove a song from an existing playlist."""
        try:
            playlist_manager = Select()
            playlist_manager.remove_song_from_playlist(playlist_name, song_name)
        except Exception as e:
            console.print(
                f"[bold red]Error removing song from playlist:[/bold red] {str(e)}"
            )

    def move_song_in_playlist(self, direction="up", playlist_name=None, song_name=None):
        """Move a song up or down within a playlist."""
        try:
            playlist_manager = Select()
            playlist_manager.move_song_in_playlist(playlist_name, song_name, direction)
        except Exception as e:
            console.print(
                f"[bold red]Error moving song in playlist:[/bold red] {str(e)}"
            )

    def delete_playlist(self, saved_downloaded=None, playlist_name=""):
        """Delete a playlist."""
        delete_playlist = DeletePlaylist()

        if saved_downloaded is None:
            saved_downloaded = questionary.select(
                "Select Playlist Type to Delete",
                choices=["Saved Playlists", "Downloaded Playlists"],
            ).ask()

            saved_downloaded = "s" if saved_downloaded == "Saved Playlists" else "d"

        try:
            match saved_downloaded:
                case "s":
                    with console.status("[cyan]Removing saved playlist...[/cyan]"):
                        delete_playlist.delete_saved_playlist(playlist_name)
                case "d":
                    with console.status("[cyan]Removing downloaded playlist...[/cyan]"):
                        delete_playlist.delete_downloaded_playlist(playlist_name)
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")

    def setup_spotify(self):
        """Set up Spotify API credentials."""
        try:
            spotify_setup = SpotifySetup()
            if spotify_setup.setup_credentials():
                console.print("[green]Spotify setup completed successfully.[/green]")
                console.print(
                    "You can now use [bold]import_playlist[/bold] to import your Spotify playlists."
                )
            else:
                console.print("[yellow]Spotify setup was not completed.[/yellow]")
        except Exception as e:
            console.print(f"[bold red]Error during Spotify setup:[/bold red] {str(e)}")

    def import_playlist(self):
        """Import playlists from Spotify."""
        try:
            credentials_file = (
                _path_manager.app_dir / "credentials" / "spotify_credentials.json"
            )

            # Check if credentials exist
            if not credentials_file.exists():
                console.print("[yellow]Spotify credentials not found.[/yellow]")
                setup_now = questionary.confirm(
                    "Would you like to set up Spotify now?", default=True
                ).ask()

                if setup_now:
                    if not self.setup_spotify():
                        return
                else:
                    console.print(
                        "[yellow]Spotify setup is required to import playlists.[/yellow]"
                    )
                    console.print(
                        "Use the [bold]setup_spotify[/bold] command to set up."
                    )
                    return

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
                return

            # Create the importer instance
            importer = ImportSpotifyPlaylist()

            # Set a reasonable timeout for the operation
            import signal

            def timeout_handler(signum, frame):
                raise TimeoutError("Spotify connection timed out")

            # Set 60 second timeout
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(60)

            try:
                console.print("[cyan]Connecting to Spotify...[/cyan]")
                importer.import_spotify_playlist()
                # Turn off the alarm
                signal.alarm(0)
            except TimeoutError:
                console.print("[bold red]Connection to Spotify timed out.[/bold red]")
                console.print("This usually happens due to authentication issues.")

                # Offer alternative
                help_path = (
                    _path_manager.app_dir / "services" / "spotify" / "auth_helper.py"
                )
                console.print(
                    f"Try running the standalone auth helper: [cyan]python {help_path}[/cyan]"
                )
            except KeyboardInterrupt:
                # Turn off the alarm
                signal.alarm(0)
                console.print("\n[yellow]Operation cancelled by user.[/yellow]")

        except ValueError as e:
            console.print(f"[yellow]{str(e)}[/yellow]")
        except Exception as e:
            console.print(f"[bold red]Error importing playlist:[/bold red] {str(e)}")

    def download_playlist(self, playlist_name=None):
        """Download a playlist."""
        try:
            with console.status("[cyan]Preparing to download playlist...[/cyan]"):
                downloader = DownloadPlaylist()
            downloader.download_playlist(playlist_name)
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")

    def song_searched(self, song):
        """Handle a song search - either single song or comma-separated list."""
        if "," in song:
            songs = [s.strip() for s in song.split(",")]
            play_song_sequence(songs)
        else:
            ListenSongOnline(song).listen_song_online()

    def show_queue(self):
        """Show the current song queue."""
        self.queue_manager.display_queue()

    def clear_queue(self):
        """Clear the current song queue."""
        self.queue_manager.clear_queue()
        self.console.print("[green]Queue cleared successfully[/green]")

    def add_to_queue(self, song):
        """Add a song to the queue."""
        self.queue_manager.add_to_queue([song])
        self.console.print(f"[green]Added to queue:[/green] {song}")

    def show_history(self):
        """Show the song play history."""
        history_manager = RecentlyPlayedManager()
        history_manager.display_history()

    def play_previous(self):
        """Play the previous song from history."""
        history_manager = RecentlyPlayedManager()

        with console.status("[cyan]Finding previous song...[/cyan]") as status:
            prev_song = history_manager.get_previous_song()

        if prev_song:
            console.print(
                f"[bold green]Playing previous song:[/bold green] {prev_song}"
            )
            ListenSongOnline(prev_song).listen_song_online()
        else:
            console.print(
                Panel(
                    "No previous songs found in history",
                    title="History",
                    border_style="yellow",
                )
            )

    def clear_history(self):
        """Clear the song play history."""
        with console.status("[cyan]Clearing song history...[/cyan]"):
            history_manager = RecentlyPlayedManager()
            history_manager.clear_history()
        console.print("[green]Song history cleared successfully[/green]")

    def toggle_lyrics(self):
        """Toggle lyrics display on/off."""
        settings = LoadDefaultSettings()
        current_setting = settings.settings.get("show-lyrics", "yes")

        # Toggle the setting
        new_setting = "no" if current_setting.lower() == "yes" else "yes"

        # Update the setting
        updater = UpdateSpecifiedSettings("show-lyrics")
        updater.update_specified_setting_directly(new_setting)

        # Show confirmation
        status = "ON" if new_setting.lower() == "yes" else "OFF"
        self.console.print(f"[green]Lyrics display: {status}[/green]")

    def show_cache_info(self):
        """Display information about cached data."""
        from ..utils.path_manager import PathManager

        _path_manager = PathManager()

        # Create a table for the cache info
        table = Table(title="🗄️ Cache Information", box=ROUNDED, border_style="cyan")
        table.add_column("Cache Type", style="bold green")
        table.add_column("Entries", style="cyan")
        table.add_column("Size", style="magenta")
        table.add_column("Oldest Entry", style="blue")

        # Get lyrics cache info
        try:
            if _path_manager.lyrics_cache_db.exists():
                with sqlite3.connect(_path_manager.lyrics_cache_db) as conn:
                    cursor = conn.cursor()

                    # Count entries
                    cursor.execute("SELECT COUNT(*) FROM lyrics_cache")
                    count = cursor.fetchone()[0]

                    # Get oldest entry
                    cursor.execute("SELECT MIN(fetched_at) FROM lyrics_cache")
                    oldest = cursor.fetchone()[0]
                    if oldest:
                        oldest_date = time.strftime("%Y-%m-%d", time.localtime(oldest))
                    else:
                        oldest_date = "N/A"

                    # Get file size
                    size = _path_manager.lyrics_cache_db.stat().st_size
                    size_str = f"{size / 1024:.1f} KB"

                    table.add_row("Lyrics", str(count), size_str, oldest_date)
            else:
                table.add_row("Lyrics", "0", "0 KB", "N/A")

            # Add more cache types here as needed

            self.console.print(table)

        except Exception as e:
            self.console.print(
                f"[bold red]Error getting cache info:[/bold red] {str(e)}"
            )

    def cleanup_cache(self, days=30):
        """Clean up old cached data."""
        days_to_keep = days
        if isinstance(days, str) and days.isdigit():
            days_to_keep = int(days)

        with self.console.status("[cyan]Cleaning up cache...[/cyan]"):
            results = cleanup_all_caches(days_to_keep)

        if sum(results.values()) > 0:
            self.console.print(f"[green]Cache cleanup complete:[/green]")
            for cache_type, count in results.items():
                if count > 0:
                    self.console.print(
                        f"  - {cache_type.title()}: {count} entries deleted"
                    )
        else:
            self.console.print("[green]Cache is already clean![/green]")
