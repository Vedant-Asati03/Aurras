from time import sleep
from pathlib import Path
from rich.console import Console

from config import path
from src.scripts.downloadsong import SongDownloader
from src.scripts.playlist.select_playlist_from_db import Select


class DownloadPlaylist:
    """
    Class for downloading playlists.
    """

    def __init__(self):
        """Initialize the DownloadPlaylist class."""
        self.console = Console()
        self.select_playlist = None
        self.downloaded_playlist_path = None
        self.download = None
        path.downloaded_playlists.mkdir(parents=True, exist_ok=True)

    def _get_playlist_from_db(self, playlist_name):
        self.select_playlist = Select()
        if playlist_name is None:
            self.select_playlist.select_playlist_from_db()
        else:
            self.select_playlist.active_playlist = playlist_name

    def _get_songs_from_active_playlist(self):
        self.select_playlist.songs_from_active_playlist()

    def _generate_download_playlist_path(self):
        self.downloaded_playlist_path = Path(
            path.downloaded_playlists, self.select_playlist.active_playlist.lower()
        )
        self.download = SongDownloader(
            self.select_playlist.songs_in_active_playlist,
            self.downloaded_playlist_path,
        )
        self.downloaded_playlist_path.mkdir(parents=True, exist_ok=True)

    def download_playlist(self, playlist_name):
        """Download the specified playlist."""
        self._get_playlist_from_db(playlist_name)
        self._get_songs_from_active_playlist()
        self._generate_download_playlist_path()

        self.console.print(
            f"Downloading Playlist - {self.select_playlist.active_playlist}\n\n",
            style="#D09CFA",
        )

        self.download.download_song()

        self.console.print("Download complete.", style="#D09CFA")
        sleep(1)
