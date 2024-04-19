import sqlite3
import shutil
from time import sleep
import questionary
from rich.console import Console

from config import path
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
        self.select = Select()
        self.config = path.Config()
        self.downloaded_playlists = None

    def delete_saved_playlist(self, playlist_name):
        """Delete a saved playlist."""
        # print(f"|{playlist_name}|")
        if playlist_name == "":
            self.select.select_playlist_from_db()
        else:
            self.select.active_playlist = playlist_name

        with sqlite3.connect(path.saved_playlists) as playlist:
            cursor = playlist.cursor()
            cursor.execute(f"DROP TABLE IF EXISTS '{self.select.active_playlist}'")
            self.console.print(f"Removed playlist - {self.select.active_playlist}")
            sleep(1.5)

    def delete_downloaded_playlist(self, playlist_name):
        """Delete a downloaded playlist."""
        self.downloaded_playlists = self.config.list_directory(
            path.downloaded_playlists
        )

        if playlist_name == "":
            accessed_playlist = questionary.select(
                "Select a playlist to delete", choices=self.downloaded_playlists
            ).ask()
        else:
            accessed_playlist = playlist_name

        shutil.rmtree(_ := path.downloaded_playlists / accessed_playlist)
        self.console.print(f"Removed playlist - {accessed_playlist}")
        sleep(1.5)
