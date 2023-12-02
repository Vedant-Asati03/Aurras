from time import sleep
from pathlib import Path
from rich.console import Console

import config.config as path
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
        path.downloaded_playlists.mkdir(parents=True, exist_ok=True)

        self._get_playlist_from_db()
        self.downloaded_playlist_path.mkdir(parents=True, exist_ok=True)

    def _get_playlist_from_db(self):
        self.select_playlist = Select()
        self.select_playlist.select_playlist_from_db()
        self.downloaded_playlist_path = Path(
            path.downloaded_playlists, self.select_playlist.active_playlist
        )
        self.download = SongDownloader(
            self.select_playlist.songs_in_active_playlist,
            self.downloaded_playlist_path,
        )

    def download_playlist(self):
        """Download the specified playlist."""
        self.console.print(
            f"Downloading Playlist - {self.select_playlist.active_playlist}\n\n",
            style="#D09CFA",
        )

        self.download.download_song()

        self.console.print("Download complete.", style="#D09CFA")
        sleep(1)
