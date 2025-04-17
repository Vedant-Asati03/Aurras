"""
Cache Initialization Module

This module provides a class for initializing the playlist database.
"""

import sqlite3

from ...utils.path_manager import PathManager

_path_manager = PathManager()
playlist_db_path = _path_manager.playlists_db


class InitializePlaylistDatabase:
    """
    Class for initializing the playlist database.
    """

    def initialize_cache(self):
        """
        Initializes the cache database with the required tables.
        """
        with sqlite3.connect(playlist_db_path) as db:
            cursor = db.cursor()

            # Create playlists table
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS playlists (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at INTEGER,
                    updated_at INTEGER
                )"""
            )

            # Create playlist_songs table
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS playlist_songs (
                    id INTEGER PRIMARY KEY,
                    playlist_id INTEGER,
                    track_name TEXT,
                    url TEXT,
                    artist_name TEXT,
                    album_name TEXT,
                    thumbnail_url TEXT,
                    duration INTEGER DEFAULT 0,
                    added_at INTEGER,
                    FOREIGN KEY (playlist_id) REFERENCES playlists(id)
                )"""
            )
