"""
Authenticate with Spotify
"""
import os
import sqlite3

from rich.console import Console

console = Console()


def authenticate_spotify():
    """
    This function allows user to authenticate with Spotify
    """
    path_authfile = os.path.join(
        os.path.expanduser("~"),
        ".aurras",
        "spotify_auth.db",
    )

    with sqlite3.connect(path_authfile) as auth:

        cursor = auth.cursor()

        cursor.execute(
            """CREATE TABLE IF NOT EXISTS spotify_auth (client_id TEXT, client_secret TEXT, redirect_uri TEXT, username TEXT, scope TEXT)"""
        )

        console.print(
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
