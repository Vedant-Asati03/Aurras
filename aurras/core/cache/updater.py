"""
Cache Update Module

This module provides a class for updating the search history database.
"""

import sqlite3
import time

# Replace absolute import
from ...utils.path_manager import PathManager

_path_manager = PathManager()

from .initialize import InitializeSearchHistoryDatabase


class UpdateSearchHistoryDatabase:
    """
    Class for updating the search history database.
    """

    def __init__(self) -> None:
        """Initialize the cache if needed."""
        InitializeSearchHistoryDatabase().initialize_cache()

    def save_to_cache(
        self,
        song_user_searched,
        track_name,
        url,
        artist_name="",
        album_name="",
        thumbnail_url="",
        duration=0,
    ):
        """
        Saves the searched song and its metadata to the cache.

        Args:
            song_user_searched (str): The song query entered by the user
            track_name (str): The actual name of the song as found
            url (str): The URL of the song
            artist_name (str): The artist name
            album_name (str): The album name
            thumbnail_url (str): URL to the song's thumbnail image
            duration (int): Duration of the song in seconds
        """
        with sqlite3.connect(_path_manager.cache_db) as cache_db:
            cursor = cache_db.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO cache 
                (song_user_searched, track_name, url, 
                 artist_name, album_name, thumbnail_url, duration, fetch_time) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    song_user_searched,
                    track_name,
                    url,
                    artist_name,
                    album_name,
                    thumbnail_url,
                    duration,
                    int(time.time()),
                ),
            )
            return cursor.lastrowid

    def save_lyrics(self, cache_id, synced_lyrics="", plain_lyrics=""):
        """
        Saves lyrics for a cached song.

        Args:
            cache_id (int): The ID of the cache entry to associate lyrics with
            synced_lyrics (str): Timed/synced lyrics
            plain_lyrics (str): Plain text lyrics
        """
        if not cache_id:
            return

        with sqlite3.connect(_path_manager.cache_db) as cache_db:
            cursor = cache_db.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO lyrics
                (cache_id, synced_lyrics, plain_lyrics, fetch_time)
                VALUES (?, ?, ?, ?)
                """,
                (cache_id, synced_lyrics, plain_lyrics, int(time.time())),
            )

    def save_full_song_data(
        self,
        song_user_searched,
        track_name,
        url,
        artist_name="",
        album_name="",
        thumbnail_url="",
        duration=0,
        synced_lyrics="",
        plain_lyrics="",
    ):
        """
        Save complete song data including metadata and lyrics in one call.

        Args:
            song_user_searched (str): The song query entered by the user
            track_name (str): The actual name of the song as found
            url (str): The URL of the song
            artist_name (str): The artist name
            album_name (str): The album name
            thumbnail_url (str): URL to the song's thumbnail image
            duration (int): Duration of the song in seconds
            synced_lyrics (str): Timed/synced lyrics
            plain_lyrics (str): Plain text lyrics
        """
        with sqlite3.connect(_path_manager.cache_db) as cache_db:
            # Start a transaction
            cache_db.execute("BEGIN TRANSACTION")
            try:
                # Save metadata
                cache_id = self.save_to_cache(
                    song_user_searched,
                    track_name,
                    url,
                    artist_name,
                    album_name,
                    thumbnail_url,
                    duration,
                )

                # Save lyrics if provided
                if (synced_lyrics or plain_lyrics) and cache_id:
                    self.save_lyrics(cache_id, synced_lyrics, plain_lyrics)

                # Commit the transaction
                cache_db.execute("COMMIT")
            except Exception as e:
                # Rollback on error
                cache_db.execute("ROLLBACK")
                raise e
