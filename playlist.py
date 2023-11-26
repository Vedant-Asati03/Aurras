"""
This module provides a playlist management system with classes for downloading, deleting, importing from Spotify, and playing playlists.

Classes:
- PlaylistManager: Base class for managing playlists.
  - Attributes:
    - console: Instance of the rich.Console class for enhanced console output.

- DownloadPlaylist: Class for downloading playlists.
  - Methods:
    - download_playlist(): Download the specified playlist.

- DeletePlaylist: Class for deleting playlists.
  - Methods:
    - delete_saved_playlist(self): Delete a saved playlist.
    - delete_downloaded_playlist(self): Delete a downloaded playlist.

- ImportPlaylist: Class for importing playlists from Spotify.
  - Attributes:
    - spotify_auth: Instance of the SpotifyAuthenticator class for Spotify authentication.
  - Methods:
    - _retrieve_user_playlists_from_spotify(): Retrieve the user's Spotify playlists.
    - _get_playlist_to_import(): Get the user's selection of a playlist to import.
    - _track_spotify_playlist(): Track songs from a Spotify playlist and store in the local database.
    - import_playlist(): Import a playlist from Spotify.

Example Usage:
```python
# Import the necessary classes
from playlist_manager import DownloadPlaylist, DeletePlaylist, ImportPlaylist, PlayPlaylist

# Create an instance of DownloadPlaylist and download a playlist
download_manager = DownloadPlaylist(playlist_name="MyPlaylist", playlist_path)
download_manager.download_playlist()

# Create an instance of DeletePlaylist and delete a playlist
delete_manager = DeletePlaylist()
delete_manager.delete_playlist()

# Create an instance of ImportPlaylist and import a playlist from Spotify
import_manager = ImportPlaylist()
import_manager.import_playlist()

"""

import sqlite3
from time import sleep
from pathlib import Path

import questionary
from rich.console import Console

import config as path
from config import Config
from term_utils import clear_screen
from downloadsong import SongDownloader
from authenticatespotify import SpotifyAuthenticator


class PlaylistManager:
    """
    Base class for managing playlists.
    """

    def __init__(self):
        """
        Initialize the PlaylistManager class.
        """
        self.config = Config()
        self.console = Console()

        path.downloaded_playlists.mkdir(parents=True, exist_ok=True)


class SelectPlaylist(PlaylistManager):
    """
    Class for selecting playlist.
    """

    def __init__(self):
        """Initialize the SelectPlaylist class."""
        super().__init__()
        self.active_playlist = None
        self.songs_in_active_playlist = None

    def select_playlist_from_db(self):
        """Select a playlist from the saved playlists."""
        with sqlite3.connect(path.saved_playlists) as playlists:
            cursor = playlists.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")

            tables = cursor.fetchall()
            table_names = [table[0] for table in tables]

            self.active_playlist = questionary.select(
                "Your Playlists\n\n", choices=table_names
            ).ask()

            cursor.execute(f"SELECT playlists_songs FROM '{self.active_playlist}'")
            songs_in_active_playlist = (
                cursor.fetchall()
            )  # this is a list of tuples containing all songs in active playlist

            self.songs_in_active_playlist = [
                str(song[0]) for song in songs_in_active_playlist
            ]


class DownloadPlaylist(PlaylistManager):
    """
    Class for downloading playlists.
    """

    def __init__(self):
        """Initialize the DownloadPlaylist class."""
        super().__init__()
        self.select_playlist = SelectPlaylist()
        self.select_playlist.select_playlist_from_db()
        self.downloaded_playlist_path = Path(
            path.downloaded_playlists / self.select_playlist.active_playlist
        )
        self.download = SongDownloader(
            self.select_playlist.songs_in_active_playlist,
            self.downloaded_playlist_path,
        )

        self.downloaded_playlist_path.mkdir(parents=True, exist_ok=True)

    def download_playlist(self):
        """Download the specified playlist."""
        self.console.print(
            f"Downloading Playlist - {self.select_playlist.active_playlist}\n\n",
            style="#D09CFA",
        )

        self.download.download_song()

        self.console.print("Download complete.", style="#D09CFA")
        sleep(1)


class DeletePlaylist(PlaylistManager):
    """
    Class for deleting playlists.
    """

    def __init__(self):
        """
        Initialize the DeletePlaylist class.
        """
        super().__init__()
        self.select_playlist = SelectPlaylist()
        self.select_playlist.select_playlist_from_db()
        self.downloaded_playlists = self.config.list_directory(
            path.downloaded_playlists
        )

    def delete_saved_playlist(self):
        """Delete a saved playlist."""
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
        accessed_playlist = questionary.select(
            "Select a playlist to delete", choices=self.downloaded_playlists
        ).ask()

        (_ := path.downloaded_playlists / accessed_playlist).rmdir()
        self.console.print(f"Removed playlist - {accessed_playlist}")
        sleep(1.5)


class ImportPlaylist(PlaylistManager):
    """
    Class for importing playlists from Spotify.
    """

    def __init__(self):
        """
        Initialize the ImportPlaylist class.
        """
        super().__init__()
        self.spotify_auth = SpotifyAuthenticator()
        self.spotify_conn = None
        self.spotify_user_playlists = None
        self.playlist_to_import = None
        self.name_id_mapping = None
        self._retrieve_user_playlists_from_spotify()

        if not path.spotify_auth.exists():
            self.spotify_auth.store_spotify_credentials()
        else:
            pass

    def _retrieve_user_playlists_from_spotify(self):
        """
        Retrieve the user's Spotify playlists.

        Returns:
            tuple: A tuple containing playlists and the Spotify connection object.
        """
        self.spotify_conn = self.spotify_auth.connect_to_spotify()
        self.spotify_user_playlists = self.spotify_conn.current_user_playlists()

    def _get_playlist_to_import(self):
        """
        Get the user's selection of a playlist to import.
        """
        my_spotify_playlists = [
            my_playlist["name"] for my_playlist in self.spotify_user_playlists["items"]
        ]

        self.playlist_to_import = questionary.select(
            "Your Spotify Playlists", choices=my_spotify_playlists
        ).ask()

    def _track_spotify_playlist(self):
        """
        Track songs from a Spotify playlist and store in the local database.
        """
        tracks = self.spotify_conn.playlist_items(
            self.name_id_mapping[self.playlist_to_import]
        )

        with sqlite3.connect(path.saved_playlists) as playlist:
            cursor = playlist.cursor()
            for track in tracks["items"]:
                cursor.execute(
                    f"CREATE TABLE IF NOT EXISTS '{self.playlist_to_import}' (id INTEGER PRIMARY KEY, playlists_songs TEXT)"
                )
                cursor.execute(
                    f"INSERT INTO '{self.playlist_to_import}' (playlists_songs) VALUES (:song)",
                    {"song": track["track"]["name"]},
                )

    def import_playlist(self):
        """
        Import a playlist from Spotify and optionally download it.
        """
        self._get_playlist_to_import()
        self.name_id_mapping = {
            playlist["name"]: playlist["id"]
            for playlist in self.spotify_user_playlists["items"]
        }

        clear_screen()

        self._track_spotify_playlist()
        self.console.print(f"Imported Playlist - {self.playlist_to_import}")
        sleep(1.5)
