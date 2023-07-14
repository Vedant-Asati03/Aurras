"""
...
"""
import os
import sqlite3

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


def recommend_songs():
    """
    This function recommend songs
    """
    path_spotifyauth = os.path.join(
        os.path.expanduser("~"), ".aurras", "spotify_auth.db"
    )
    path_recommendation = os.path.join(
        os.path.expanduser("~"), ".aurras", "recommendation.db"
    )
    path_cache = os.path.join(os.path.expanduser("~"), ".aurras", "cache.db")

    with sqlite3.connect(path_cache) as recommendation:

        cursor = recommendation.cursor()

        cursor.execute("SELECT song_name FROM cache")
        songs = cursor.fetchmany(5)

    with sqlite3.connect(path_spotifyauth) as auth:

        cursor = auth.cursor()

        cursor.execute("SELECT client_id, client_secret FROM spotify_auth")
        row = cursor.fetchone()

        client_credentials_manager = SpotifyClientCredentials(
            client_id=row[0],
            client_secret=row[1],
        )
        SP = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

        for song_name in songs:

            results = SP.search(q=song_name, limit=1, type="track")

            if len(results["tracks"]["items"]) > 0:
                song_id = results["tracks"]["items"][0]["id"]

                recommended_song = SP.recommendations(seed_tracks=[song_id], limit=1)[
                    "tracks"
                ][0]["name"]
            else:
                return []

            with sqlite3.connect(path_recommendation) as recommendation:
                cursor = recommendation.cursor()
                cursor.execute(
                    """CREATE TABLE IF NOT EXISTS recommendations (song TEXT)"""
                )

                cursor.execute(
                    "INSERT INTO recommendations (song) VALUES (:song)",
                    {"song": recommended_song},
                )

        auth.commit()
