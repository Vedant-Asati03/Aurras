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

import config.config as path
from lib.manage_spotify.spotify_auth_handler import (
    CheckSpotifyAuthenticationStatus,
)


class SongRecommendations:
    """
    Class for managing song recommendations.
    """

    def __init__(self):
        """
        Initialize SongRecommendations.
        """
        self.songs_retrieved = None
        self.spotify_auth = CheckSpotifyAuthenticationStatus()

        self._authentication_status()

    def _authentication_status(self):
        self.spotify_auth.check_if_authenticated()
        if self.spotify_auth.response is None:
            self._get_songs_from_cache()

    def _get_songs_from_cache(self):
        """
        Get songs from the cache database.

        Returns:
            list: List of song names.
        """
        with sqlite3.connect(path.cache) as recommendation:
            cursor = recommendation.cursor()

            cursor.execute("SELECT song_user_searched FROM cache")
            self.songs_retrieved = cursor.fetchmany(5)

    def _save_recommendations(self, recommended_song: str):
        """
        Save recommended songs to the recommendation database.

        Args:
            recommended_song (str): The name of the recommended song.
        """
        with sqlite3.connect(path.recommendation) as recommendation:
            cursor = recommendation.cursor()
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS recommendation (song_recommendation TEXT)"""
            )
            cursor.execute("SELECT song_recommendation FROM recommendation")

            cursor.execute(
                "INSERT INTO recommendation (song_recommendation) VALUES (:song_recommendation)",
                {"song_recommendation": recommended_song},
            )

    def recommend_songs(self):
        """
        Recommend songs based on cached songs and save them to the recommendation database.
        """
        for song_name in self.songs_retrieved:
            result = self.spotify_auth.spotify_conn.search(
                q=song_name, limit=1, type="track"
            )

            if len(result["tracks"]["items"]) > 0:
                song_id = result["tracks"]["items"][0]["id"]

                recommended_song = self.spotify_auth.spotify_conn.recommendations(
                    seed_tracks=[song_id], limit=1
                )["tracks"][0]["name"]

            self._save_recommendations(recommended_song)
