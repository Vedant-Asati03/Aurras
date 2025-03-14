import sqlite3
import shutil
from time import sleep
import questionary
from rich.console import Console

# Replace absolute import with relative import
from ..utils.path_manager import PathManager

_path_manager = PathManager()  # Create an instance to use

from ..playlist.manager import Select


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
        # Use the path manager instance instead of the imported path
        self.downloaded_playlists = None

    def delete_saved_playlist(self, playlist_name):
        """Delete a saved playlist."""
        if playlist_name == "":
            self.select.select_playlist_from_db()
        else:
            self.select.active_playlist = playlist_name

        with sqlite3.connect(_path_manager.saved_playlists) as playlist:
            cursor = playlist.cursor()
            cursor.execute(f"DROP TABLE IF EXISTS '{self.select.active_playlist}'")
            self.console.print(f"Removed playlist - {self.select.active_playlist}")
            sleep(1.5)

    def delete_downloaded_playlist(self, playlist_name):
        """Delete a downloaded playlist."""
        self.downloaded_playlists = _path_manager.list_directory(
            _path_manager.playlists_dir
        )

        if playlist_name == "":
            accessed_playlist = questionary.select(
                "Select a playlist to delete", choices=self.downloaded_playlists
            ).ask()
        else:
            accessed_playlist = playlist_name

        shutil.rmtree(_ := _path_manager.playlists_dir / accessed_playlist)
        self.console.print(f"Removed playlist - {accessed_playlist}")
        sleep(1.5)
