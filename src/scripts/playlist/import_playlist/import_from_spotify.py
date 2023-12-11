import sqlite3
from time import sleep
import questionary
from rich.console import Console

import config.config as path

from lib.term_utils import clear_screen
from lib.manage_spotify.spotify_auth_handler import (
    CheckSpotifyAuthenticationStatus,
)


class ImportSpotifyPlaylist:
    """
    Class for importing playlists from Spotify.
    """

    def __init__(self):
        """
        Initialize the ImportPlaylist class.
        """
        self.console = Console()
        self.name_id_mapping = None
        self.playlist_to_import = None
        self.spotify_user_playlists = None
        self.spotify_auth = CheckSpotifyAuthenticationStatus()

        self._authentication_status()

    def _authentication_status(self):
        self.spotify_auth.check_if_authenticated()

        if self.spotify_auth.response is None:
            self._retrieve_user_playlists_from_spotify()

    def _retrieve_user_playlists_from_spotify(self):
        """
        Retrieve the user's Spotify playlists.
        """
        self.spotify_user_playlists = (
            self.spotify_auth.spotify_conn.current_user_playlists()
        )

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
        tracks = self.spotify_auth.spotify_conn.playlist_items(
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

    def import_spotify_playlist(self):
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
