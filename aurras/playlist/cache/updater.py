"""
Cache Update Module

This module provides a class for updating the playlist database.
"""

import time
import sqlite3
from typing import List

from .initialize import InitializePlaylistDatabase
from ...utils.path_manager import PathManager

_path_manager = PathManager()
playlist_db_path = _path_manager.playlists_db


class UpdatePlaylistDatabase:
    """
    Class for updating the playlist database.
    """

    def __init__(self) -> None:
        """Initialize the playlist database if needed."""
        InitializePlaylistDatabase().initialize_cache()

    def save_playlist(
        self,
        playlist_name: str,
        description: str = "",
        created_at: int = 0,
        updated_at: int = 0,
    ) -> None:
        """
        Saves a new playlist to the database.

        Args:
            playlist_name (str): The name of the playlist
            description (str): Description of the playlist
            created_at (int): Timestamp when the playlist was created
            updated_at (int): Timestamp when the playlist was last updated
        """
        with sqlite3.connect(playlist_db_path) as db:
            cursor = db.cursor()
            cursor.execute(
                """
                INSERT INTO playlists (name, description, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (playlist_name, description, created_at, updated_at),
            )
            db.commit()
            return cursor.lastrowid

    def save_song_to_playlist(
        self,
        playlist_id: int,
        track_name: str,
        url: str,
        artist_name: str = "",
        album_name: str = "",
        thumbnail_url: str = "",
        duration: int = 0,
    ) -> None:
        """
        Saves a song to a specific playlist.

        Args:
            playlist_id (int): The ID of the playlist
            track_name (str): The name of the song
            url (str): The URL of the song
            artist_name (str): The artist name
            album_name (str): The album name
            thumbnail_url (str): URL to the song's thumbnail image
            duration (int): Duration of the song in seconds
        """
        with sqlite3.connect(playlist_db_path) as db:
            cursor = db.cursor()
            cursor.execute(
                """
                INSERT INTO playlist_songs 
                (playlist_id, track_name, url, artist_name, album_name, thumbnail_url, duration, added_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    playlist_id,
                    track_name,
                    url,
                    artist_name,
                    album_name,
                    thumbnail_url,
                    duration,
                    int(time.time()),
                ),
            )
            db.commit()
            return cursor.lastrowid

    def remove_playlist(self, playlist_names: List[str]) -> None:
        """
        Removes playlists from the database.

        Args:
            playlist_names (List[str]): List of playlist names to be removed
        """
        with sqlite3.connect(playlist_db_path) as db:
            cursor = db.cursor()
            cursor.execute(
                """
                DELETE FROM playlists 
                WHERE name IN ({})
                """.format(",".join("?" * len(playlist_names))),
                playlist_names,
            )
            db.commit()
            return cursor.rowcount

    def remove_song_from_playlist(
        self, playlist_name: str, song_name: List[str]
    ) -> None:
        """
        Removes a song from a specific playlist.

        Args:
            playlist_name (str): The name of the playlist
            song_name (List[str]): List of song names to be removed
        """
        with sqlite3.connect(playlist_db_path) as db:
            cursor = db.cursor()
            cursor.execute(
                """
                DELETE FROM playlist_songs 
                WHERE playlist_id = (SELECT id FROM playlists WHERE name = ?)
                AND track_name IN ({})
                """.format(",".join("?" * len(song_name))),
                [playlist_name] + song_name,
            )
            db.commit()
            return cursor.rowcount
