"""
Authenticate with Spotify
"""
import json
import os

from rich.console import Console

console = Console()


def authenticate_spotify():
    """
    This function allows user to authenticate with Spotify
    """

    try:
        if "spotify_auth.json" not in os.listdir(
            os.path.join(os.path.expanduser("~"), ".aurras")
        ):

            console.print(
                "Create your client_id and client_secret from Spotify Developer-\n[#E3ACF9]Click Here: https://developer.spotify.com/dashboard/\n",
                style="#EAE0DA",
            )

            client_id = input("Paste Spotify client_id: ")
            client_secret = input("Paste Spotify client_secret: ")
            redirect_uri = input("Paste redirect_uri: ")
            username = input("Write your Spotify username: ")

            spotify_auth = {
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "username": username,
                "scope": "playlist-read-private",
            }

            with open(
                os.path.join(
                    os.path.expanduser("~"),
                    ".aurras",
                    "spotify_auth.json",
                ),
                "w",
                encoding="UTF-8",
            ) as credential_data:

                json.dump(spotify_auth, credential_data, indent=4)

    except:
        pass
