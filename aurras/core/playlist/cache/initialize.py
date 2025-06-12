"""
Cache Initialization Module

This module provides a class for initializing the playlist database.
"""


class InitializePlaylistDatabase:
    """
    Class for initializing the playlist database.
    """

    def initialize_cache(self, connection=None):
        """
        Initializes the cache database with the required tables.

        Args:
            connection: An optional pre-existing database connection. If not provided,
                       a new connection will be created for initialization.
        """
        if connection:
            self._initialize_tables(connection)
        else:
            from aurras.utils.db_connection import DatabaseConnectionManager
            from aurras.utils.path_manager import _path_manager

            with DatabaseConnectionManager(_path_manager.playlists_db) as db:
                self._initialize_tables(db)

    def _initialize_tables(self, connection):
        """
        Initializes the cache database with the required tables.
        """
        cursor = connection.cursor()

        # Create playlists table
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS playlists (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                updated_at INTEGER,
                is_downloaded BOOLEAN DEFAULT FALSE
            )"""
        )

        cursor.execute(
            """CREATE TABLE IF NOT EXISTS playlist_songs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                playlist_id INTEGER,
                track_name TEXT NOT NULL,
                artist_name TEXT,
                added_at INTEGER,
                FOREIGN KEY (playlist_id) REFERENCES playlists(id),
                UNIQUE(playlist_id, track_name, artist_name)
            )"""
        )
