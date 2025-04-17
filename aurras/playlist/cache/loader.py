"""
Cache Loading Module

This module provides a class for loading data from the playlist database.
"""

from ...utils.path_manager import PathManager
from .initialize import InitializePlaylistDatabase

import sqlite3
from typing import List, Dict, Any


_path_manager = PathManager()
playlist_db_path = _path_manager.playlists_db


class LoadPlaylistData:
    """
    Class for loading playlist data from the database.
    """

    def __init__(self) -> None:
        """Initialize the playlist database if needed."""
        InitializePlaylistDatabase().initialize_cache()

    def load_playlists(self) -> List[Dict[str, Any]]:
        """
        Loads all playlists from the database.

        Returns:
            list: A list of dictionaries containing playlist metadata
        """
        with sqlite3.connect(playlist_db_path) as db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM playlists")
            return [
                {
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "created_at": row[3],
                    "updated_at": row[4],
                }
                for row in cursor.fetchall()
            ]

    def load_playlist_songs_with_full_metadata(
        self, playlist_name: int
    ) -> List[Dict[str, Any]]:
        """
        Loads songs from a specific playlist.

        Args:
            playlist_name (int): The ID of the playlist.

        Returns:
            list: A list of dictionaries containing song metadata
        """
        with sqlite3.connect(playlist_db_path) as db:
            cursor = db.cursor()
            cursor.execute(
                """SELECT * FROM playlist_songs WHERE playlist_id = ?""",
                (playlist_name,),
            )
            return [
                {
                    "id": row[0],
                    "playlist_id": row[1],
                    "track_name": row[2],
                    "url": row[3],
                    "artist_name": row[4],
                    "album_name": row[5],
                    "thumbnail_url": row[6],
                    "duration": row[7],
                    "added_at": row[8],
                }
                for row in cursor.fetchall()
            ]
