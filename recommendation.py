"""
Song Recommendations Module

This module provides a class for managing song recommendations based on cached songs.

Example:
    ```python
    recommendations_manager = SongRecommendations()
    recommendations_manager.recommend_songs()
    ```

Classes:
    - SongRecommendations: Class for managing song recommendations.

Attributes:
    - SpotifyAuthenticator: Class for authenticating with Spotify.
    - path: Module for handling file paths.

Methods:
    - get_songs_from_cache: Get songs from the cache database.
    - recommend_songs: Recommend songs based on cached songs and save them to the recommendation database.
    - save_recommendations: Save recommended songs to the recommendation database.
"""

import sqlite3

import config as path
from authenticatespotify import SpotifyAuthenticator


class SongRecommendations:
    """
    Class for managing song recommendations.
    """

    def __init__(self):
        """
        Initialize SongRecommendations.
        """
        self.spotify_auth = SpotifyAuthenticator()

    def get_songs_from_cache(self):
        """
        Get songs from the cache database.

        Returns:
            list: List of song names.
        """
        with sqlite3.connect(path.cache) as recommendation:
            cursor = recommendation.cursor()

            cursor.execute("SELECT song_name FROM cache")
            songs = cursor.fetchmany(5)

        return songs

    def recommend_songs(self):
        """
        Recommend songs based on cached songs and save them to the recommendation database.
        """
        songs = SongRecommendations().get_songs_from_cache()
        spotify_conn = self.spotify_auth.connect_to_spotify()

        for song_name in songs:
            results = spotify_conn.search(q=song_name, limit=1, type="track")

            if len(results["tracks"]["items"]) > 0:
                song_id = results["tracks"]["items"][0]["id"]

                recommended_song = spotify_conn.recommendations(
                    seed_tracks=[song_id], limit=1
                )["tracks"][0]["name"]

            SongRecommendations().save_recommendations(recommended_song)

    def save_recommendations(self, recommended_song):
        """
        Save recommended songs to the recommendation database.

        Args:
            recommended_song (str): The name of the recommended song.
        """
        with sqlite3.connect(path.recommendation) as recommendation:
            cursor = recommendation.cursor()
            cursor.execute("""CREATE TABLE IF NOT EXISTS recommendations (song TEXT)""")

            cursor.execute(
                "INSERT INTO recommendations (song) VALUES (:song)",
                {"song": recommended_song},
            )
