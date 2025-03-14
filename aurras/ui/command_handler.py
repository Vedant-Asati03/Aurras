from rich.text import Text
from rich.console import Console
import questionary

from ..core.downloader import SongDownloader
from ..playlist.delete import DeletePlaylist
from ..playlist.download import DownloadPlaylist
from ..player.online import ListenSongOnline, ListenPlaylistOnline, play_song_sequence
from ..player.offline import ListenSongOffline, ListenPlaylistOffline
from ..services.spotify.importer import ImportSpotifyPlaylist
from ..player.queue import QueueManager


class InputCases:
    def __init__(self) -> None:
        self.console = Console()
        self.queue_manager = QueueManager()

    def display_help(self):
        """Display help information about available commands."""
        self.console.print("""
[bold green]╭───────────────────────────────────────────────────╮[/]
[bold green]│              AURRAS MUSIC PLAYER HELP             │[/]
[bold green]╰───────────────────────────────────────────────────╯[/]

[bold yellow]BASIC USAGE:[/]
  - Type a song name to search and play it
  - Type multiple song names separated by commas to queue them
  - Use '?' for feature suggestions
  - Press Ctrl+C to exit

[bold yellow]QUEUE COMMANDS:[/]
  • [cyan]queue[/]                  - Display the current song queue
  • [cyan]clear_queue[/]            - Clear the current song queue
  • [cyan]song1, song2, ...[/]      - Play multiple songs in sequence

[bold yellow]COMMAND SHORTCUTS:[/]
  • [cyan]d, song1, song2, ...[/]   - Download multiple songs
  • [cyan]dp, playlist_name[/]      - Download a specific playlist
  • [cyan]pn, playlist_name[/]      - Play a saved playlist online
  • [cyan]pf, playlist_name[/]      - Play a downloaded playlist offline
  • [cyan]rs, playlist_name[/]      - Remove a saved playlist
  • [cyan]rd, playlist_name[/]      - Remove a downloaded playlist

[bold yellow]MAIN COMMANDS:[/]
  • [cyan]help[/]                   - Display this help information
  • [cyan]play_offline[/]           - Browse and play downloaded songs
  • [cyan]download_song[/]          - Download song(s) for offline listening
  • [cyan]play_playlist[/]          - Play songs from a playlist
  • [cyan]delete_playlist[/]        - Delete a playlist
  • [cyan]import_playlist[/]        - Import playlists from Spotify

[bold yellow]PLAYBACK CONTROLS:[/]
  • [cyan]q[/]                      - End current song playback
  • [cyan]p[/]                      - Pause/Resume playback
  • [cyan]t[/]                      - Translate lyrics
  • [cyan]UP/DOWN[/]                - Adjust volume
  • [cyan]Mouse wheel[/]            - Fine tune volume
""")

    def play_offline(self):
        ListenSongOffline().listen_song_offline()

    def download_song(self, songs_to_download=None):
        if songs_to_download is None or songs_to_download == []:
            songs_input = self.console.input(
                Text(
                    "Enter song name[s] (separate multiple songs with commas): ",
                    style="#A2DE96",
                )
            )
            # Split by comma and strip whitespace
            songs_to_download = [s.strip() for s in songs_input.split(",") if s.strip()]
            if not songs_to_download:
                self.console.print("No valid song names provided.")
                return

        print(f"Downloading {len(songs_to_download)} songs: {songs_to_download}")
        download = SongDownloader(songs_to_download)
        download.download_song()

    def play_playlist(self, online_offline=None, playlist_name=None):
        listen_playlist_online = ListenPlaylistOnline()
        listen_playlist_offline = ListenPlaylistOffline()

        if online_offline is None:
            online_offline = questionary.select(
                "", choices=["Play Online", "Play Offline"]
            ).ask()

            online_offline = "n" if online_offline == "Play Online" else "f"

        match online_offline:
            case "n":
                listen_playlist_online.listen_playlist_online(playlist_name)
            case "f":
                listen_playlist_offline.listen_playlist_offline(playlist_name)

    def delete_playlist(self, saved_downloaded=None, playlist_name=""):
        delete_playlist = DeletePlaylist()

        if saved_downloaded is None:
            saved_downloaded = questionary.select(
                "Select Playlist to Delete",
                choices=["Saved Playlists", "Downloaded Playlists"],
            ).ask()

            saved_downloaded = "s" if saved_downloaded == "Saved Playlists" else "d"

        match saved_downloaded:
            case "s":
                delete_playlist.delete_saved_playlist(playlist_name)
            case "d":
                print(playlist_name)
                delete_playlist.delete_downloaded_playlist(playlist_name)

    def import_playlist(self):
        ImportSpotifyPlaylist().import_spotify_playlist()

    def download_playlist(self, playlist_name=None):
        DownloadPlaylist().download_playlist(playlist_name)

    def song_searched(self, song):
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
        self.console.print("Queue cleared")

    def add_to_queue(self, song):
        """Add a song to the queue."""
        self.queue_manager.add_to_queue([song])
        self.console.print(f"Added to queue: {song}")
