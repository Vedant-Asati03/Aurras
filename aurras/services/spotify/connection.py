"""
Spotify Connection Module

This module handles connections to the Spotify API.
"""

import sqlite3
import spotipy
from spotipy import util

# Replace absolute import
from ...utils.path_manager import PathManager

_path_manager = PathManager()


class SetupSpotifyConnection:
    """
    Class for setting up a connection to the Spotify API.
    """

    def __init__(self) -> None:
        """Initialize the Spotify connection attributes."""
        self.client_id = None
        self.client_secret = None
        self.scope = None
        self.username = None
        self.redirect_uri = None
        self.spotify_conn = None

    def _fetch_auth_credentials_from_db(self):
        """Fetch authentication credentials from the database."""
        with sqlite3.connect(_path_manager.spotify_auth) as auth:
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
        """Create a connection to the Spotify API."""
        self._fetch_auth_credentials_from_db()

        token = util.prompt_for_user_token(
            client_id=self.client_id,
            client_secret=self.client_secret,
            scope=self.scope,
            username=self.username,
            redirect_uri=self.redirect_uri,
        )

        self.spotify_conn = spotipy.Spotify(auth=token)
