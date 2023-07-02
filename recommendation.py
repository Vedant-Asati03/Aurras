"""
...
"""
import os
import json
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


def recommend_songs(song_name):
    """
    This function recommend songs
    """

    with open(
        os.path.join(
            os.path.expanduser("~"),
            ".aurras",
            "spotify_auth.json",
        ),
        "r",
        encoding="UTF-8",
    ) as credential_data:

        get_credentials = credential_data.read()
        credentials = json.loads(get_credentials)

        client_credentials_manager = SpotifyClientCredentials(
            client_id=credentials["client_id"],
            client_secret=credentials["client_secret"],
        )
        SP = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

        results = SP.search(q=song_name, limit=1, type="track")

        if len(results["tracks"]["items"]) > 0:
            song_id = results["tracks"]["items"][0]["id"]

            related_songs = SP.recommendations(seed_tracks=[song_id], limit=10)[
                "tracks"
            ]

            related_song_names = [song["name"] for song in related_songs]

            with open(
                os.path.join(
                    os.path.expanduser("~"), ".aurras", "recommended_songs.txt"
                ),
                "a",
                encoding="UTF-8",
            ) as recommended_list:
                for song in related_song_names:
                    recommended_list.write(song + "\n")

        else:
            return []
