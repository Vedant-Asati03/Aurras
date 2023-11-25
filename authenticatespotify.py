"""
Spotify Authenticator Module

This module provides a class for authenticating with Spotify and storing credentials.

Example:
    ```python
    authenticator = SpotifyAuthenticator()
    authenticator.store_spotify_credentials()
    connection = authenticator.connect_to_spotify()
    ```

Classes:
    - SpotifyAuthenticator: Class for authenticating with Spotify and storing credentials.

Attributes:
    - spotipy: Spotify API library for Python.
    - path: Module for handling file paths.
    - rich.console: Library for rich text output in the console.

Methods:
    - store_spotify_credentials: Store Spotify credentials in a local SQLite database.
    - connect_to_spotify: Authenticate Spotify and get user playlists.
"""

import sqlite3

import spotipy
from spotipy import util
from rich.console import Console

import config as path


class SpotifyAuthenticator:
    """
    Class for authenticating with Spotify and storing credentials.
    """

    def __init__(self):
        """
        Initialize SpotifyAuthenticator.
        """
        self.console = Console()

    def store_spotify_credentials(self):
        """
        Store Spotify credentials in a local SQLite database.
        """
        with sqlite3.connect(path.spotify_auth) as auth:
            cursor = auth.cursor()
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS spotify_auth (client_id TEXT, client_secret TEXT, redirect_uri TEXT, username TEXT, scope TEXT)"""
            )

            self.console.print(
                "Create your client_id and client_secret from Spotify Developer-\n[#E3ACF9]Click Here: https://developer.spotify.com/dashboard/\n",
                style="#EAE0DA",
            )

            client_id = input("Paste Spotify client_id: ")
            client_secret = input("Paste Spotify client_secret: ")
            redirect_uri = input("Paste redirect_uri: ")
            username = input("Write your Spotify username: ")

            cursor.execute(
                "INSERT INTO spotify_auth (client_id, client_secret, redirect_uri, username, scope) VALUES (?, ?, ?, ?, ?)",
                (
                    client_id,
                    client_secret,
                    redirect_uri,
                    username,
                    "playlist-read-private",
                ),
            )

    def connect_to_spotify(self):
        """
        Authenticate Spotify and get user playlists.

        Returns:
            tuple: A tuple containing user playlists and the Spotify object.
        """
        with sqlite3.connect(path.spotify_auth) as auth:
            cursor = auth.cursor()
            cursor.execute(
                "SELECT client_id, client_secret, scope, username, redirect_uri FROM spotify_auth"
            )
            row = cursor.fetchone()

            token = util.prompt_for_user_token(
                client_id=row[0],
                client_secret=row[1],
                scope=row[2],
                username=row[3],
                redirect_uri=row[4],
            )

        connection = spotipy.Spotify(auth=token)

        return connection
