import sqlite3
from rich.console import Console

from config import path


class SpotifyDatabase:
    def __init__(self) -> None:
        self.client_id = None
        self.client_secret = None
        self.redirect_uri = None
        self.username = None
        self.console = Console()
        self.create_spotify_database()

    def create_spotify_database(self):
        with sqlite3.connect(path.spotify_auth) as auth:
            cursor = auth.cursor()
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS spotify_auth (client_id TEXT, client_secret TEXT, redirect_uri TEXT, username TEXT, scope TEXT)"""
            )

    def _get_auth_credentials(self):
        self.client_id = input("Paste Spotify client_id: ")
        self.client_secret = input("Paste Spotify client_secret: ")
        self.redirect_uri = input("Paste redirect_uri: ")
        self.username = input("Write your Spotify username: ")

    def _store_user_credentials_in_db(self):
        self._get_auth_credentials()

        with sqlite3.connect(path.spotify_auth) as auth:
            cursor = auth.cursor()
            cursor.execute(
                "INSERT INTO spotify_auth (client_id, client_secret, redirect_uri, username, scope) VALUES (?, ?, ?, ?, ?)",
                (
                    self.client_id,
                    self.client_secret,
                    self.redirect_uri,
                    self.username,
                    "playlist-read-private",
                ),
            )

    def setup_auth_db(self):
        self.console.print(
            "Create your client_id and client_secret from Spotify Developer-\n[#E3ACF9]Click Here: https://developer.spotify.com/dashboard/\n",
            style="#EAE0DA",
        )
        self._store_user_credentials_in_db()
