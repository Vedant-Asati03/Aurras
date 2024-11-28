import sqlite3
import spotipy
from spotipy import util

from config import path


class SetupSpotifyConnection:
    def __init__(self) -> None:
        self.client_id = None
        self.client_secret = None
        self.scope = None
        self.username = None
        self.redirect_uri = None
        self.spotify_conn = None

    def _fetch_auth_credentials_from_db(self):
        with sqlite3.connect(path.spotify_auth) as auth:
            cursor = auth.cursor()
            cursor.execute(
                "SELECT client_id, client_secret, scope, username, redirect_uri FROM spotify_auth"
            )
            credentials = cursor.fetchone()

        self.client_id = credentials[0]
        self.client_secret = credentials[1]
        self.scope = credentials[2]
        self.username = credentials[3]
        self.redirect_uri = credentials[4]

    def create_spotify_connection(self):
        self._fetch_auth_credentials_from_db()

        token = util.prompt_for_user_token(
            client_id=self.client_id,
            client_secret=self.client_secret,
            scope=self.scope,
            username=self.username,
            redirect_uri=self.redirect_uri,
        )

        self.spotify_conn = spotipy.Spotify(auth=token)
