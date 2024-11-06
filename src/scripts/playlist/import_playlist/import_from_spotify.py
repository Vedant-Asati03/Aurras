import sqlite3
from time import sleep
import questionary
from rich.console import Console

from config import path

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
        self.playlist_to_import = None
        self.spotify_user_playlists = None
        self.spotify_auth = CheckSpotifyAuthenticationStatus()

        self._retrieve_user_playlists_if_authenticated()

    def _retrieve_user_playlists_if_authenticated(self):
        self.spotify_auth.check_if_authenticated()

        if self.spotify_auth.response is None:
            self._user_playlists_from_spotify()

    def _user_playlists_from_spotify(self):
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
        user_spotify_playlists = [
            my_playlist["name"] for my_playlist in self.spotify_user_playlists["items"]
        ]

        self.playlist_to_import = questionary.select(
            "Your Spotify Playlists", choices=user_spotify_playlists
        ).ask()

    def _name_id_mapping(self):
        name_id_mapping = {
            playlist["name"]: playlist["id"]
            for playlist in self.spotify_user_playlists["items"]
        }

        return name_id_mapping

    def _track_spotify_playlist(self, playlist_to_import: str):
        """
        Track songs from a Spotify playlist and store in the local database.
        """
        name_id_mapping = self._name_id_mapping()

        tracks = self.spotify_auth.spotify_conn.playlist_items(
            name_id_mapping[playlist_to_import]
        )

        return tracks

    def _save_playlist_to_db(self, playlist_to_import: str):
        tracks = self._track_spotify_playlist(playlist_to_import)

        with sqlite3.connect(path.saved_playlists) as playlist:
            cursor = playlist.cursor()
            for track in tracks["items"]:
                cursor.execute(
                    f"CREATE TABLE IF NOT EXISTS '{playlist_to_import.lower()}' (id INTEGER PRIMARY KEY, playlists_songs TEXT)"
                )
                cursor.execute(
                    f"INSERT INTO '{playlist_to_import.lower()}' (playlists_songs) VALUES (:song)",
                    {"song": track["track"]["name"]},
                )

    def import_spotify_playlist(self):
        """
        Import a playlist from Spotify and optionally download it.
        """
        print("sada")
        self._get_playlist_to_import()

        clear_screen()

        self._save_playlist_to_db(self.playlist_to_import)
        self.console.print(f"Imported Playlist - {self.playlist_to_import}")
        sleep(1.5)
