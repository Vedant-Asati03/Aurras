import sqlite3
from time import sleep
import questionary
from rich.console import Console

import config.config as path
from src.scripts.playlist.select_playlist_from_db import Select


class DeletePlaylist:
    """
    Class for deleting playlists.
    """

    def __init__(self):
        """
        Initialize the DeletePlaylist class.
        """
        self.console = Console()
        self.config = path.Config()
        self.select_playlist = None
        self.downloaded_playlists = None

    def _get_playlist__from_db(self):
        self.select_playlist = Select()
        self.select_playlist.select_playlist_from_db()

    def delete_saved_playlist(self):
        """Delete a saved playlist."""
        self._get_playlist__from_db()

        with sqlite3.connect(path.saved_playlists) as playlist:
            cursor = playlist.cursor()
            cursor.execute(
                f"DROP TABLE IF EXISTS '{self.select_playlist.active_playlist}'"
            )
            self.console.print(
                f"Removed playlist - {self.select_playlist.active_playlist}"
            )
            sleep(1.5)

    def delete_downloaded_playlist(self):
        """Delete a downloaded playlist."""
        self.downloaded_playlists = self.config.list_directory(
            path.downloaded_playlists
        )

        accessed_playlist = questionary.select(
            "Select a playlist to delete", choices=self.downloaded_playlists
        ).ask()

        (_ := path.downloaded_playlists / accessed_playlist).rmdir()
        self.console.print(f"Removed playlist - {accessed_playlist}")
        sleep(1.5)
