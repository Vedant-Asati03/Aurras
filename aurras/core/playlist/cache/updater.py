"""
Cache Update Module

This module provides a class for updating the playlist database.
"""

import time
import sqlite3
from typing import List, Dict, Any, Tuple

from .initialize import InitializePlaylistDatabase
from ....utils.path_manager import PathManager

_path_manager = PathManager()
playlist_db_path = _path_manager.playlists_db


class PlaylistDatabaseConnection:
    """Singleton database connection manager for playlists."""

    _instance = None
    _connection = None

    def __new__(cls, db_path=playlist_db_path):
        if cls._instance is None:
            cls._instance = super(PlaylistDatabaseConnection, cls).__new__(cls)
            cls._instance.db_path = db_path
        return cls._instance

    def get_connection(self) -> sqlite3.Connection:
        """Get or create a database connection."""
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path)
            self._connection.row_factory = sqlite3.Row
        return self._connection

    def close(self) -> None:
        """Close the database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None


class UpdatePlaylistDatabase:
    """
    Class for updating the playlist database.
    """

    def __init__(self) -> None:
        """Initialize the playlist database if needed."""
        InitializePlaylistDatabase().initialize_cache()
        self.db_conn = PlaylistDatabaseConnection()

    def save_playlist(
        self,
        playlist_name: str,
        description: str = "",
        updated_at: int = 0,
    ) -> None:
        """
        Saves a new playlist to the database.

        Args:
            playlist_name (str): The name of the playlist
            description (str): Description of the playlist
            updated_at (int): Timestamp when the playlist was last updated
        """
        try:
            with self.db_conn.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO playlists (name, description, updated_at)
                    VALUES (?, ?, ?)
                    """,
                    (playlist_name, description, updated_at),
                )
                conn.commit()

        except sqlite3.Error as e:
            print(f"Error saving playlist '{playlist_name}': {e}")
            raise

    def _get_playlist_id(self, playlist_name: str) -> int:
        """
        Retrieves the ID of a playlist by its name.

        Args:
            playlist_name (str): The name of the playlist

        Returns:
            int: The ID of the playlist
        """
        with self.db_conn.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM playlists WHERE name = ?", (playlist_name,))
            result = cursor.fetchone()
            return result[0] if result else None

    def save_song_to_playlist(
        self,
        songs_metadata: List[tuple],
    ) -> None:
        """
        Saves a song to a specific playlist.

        Args:
            batch_data (List[tuple]): List of tuples containing song metadata
                (playlist_id, track_name, artist_name, album_name, added_at)
        """
        try:
            with self.db_conn.get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(
                    """
                    INSERT OR REPLACE INTO playlist_songs 
                    (playlist_id, track_name, artist_name, album_name, added_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    songs_metadata,
                )
                conn.commit()

        except sqlite3.Error as e:
            print(f"Error saving songs to playlist: {e}")
            raise

    def batch_save_songs_to_playlist(
        self, playlist_name: str, songs_metadata: List[tuple]
    ) -> None:
        """
        Save multiple songs to a playlist in a batch operation.

        Args:
            playlist_name (str): The name of the playlist to add songs to
            songs_metadata (List[tuple]): List of tuples containing song metadata
                (playlist_id, track_name, artist_name, album_name, added_at)
        """
        current_time = int(time.time())

        self.save_playlist(
            playlist_name=playlist_name,
            description=f"Playlist {playlist_name}",
            updated_at=current_time,
        )

        playlist_id = self._get_playlist_id(playlist_name)
        if playlist_id is None:
            raise ValueError(f"Playlist '{playlist_name}' not found in the database.")

        playlist_songs_metadata_batch: List[tuple] = [
            (
                playlist_id,
                data[0],  # track_name
                data[1],  # artist_name
                data[2],  # album_name
                data[4],  # added_at - same timestamp for batch
            )
            for data in songs_metadata
        ]

        self.save_song_to_playlist(playlist_songs_metadata_batch)

    def remove_playlist(self, playlist_names: List[str]) -> None:
        """
        Removes playlists from the database.

        Args:
            playlist_names (List[str]): List of playlist names to be removed
        """
        with self.db_conn.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                DELETE FROM playlists 
                WHERE name IN ({})
                """.format(",".join("?" * len(playlist_names))),
                playlist_names,
            )
            conn.commit()
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
        with self.db_conn.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                DELETE FROM playlist_songs 
                WHERE playlist_id = (SELECT id FROM playlists WHERE name = ?)
                AND track_name IN ({})
                """.format(",".join("?" * len(song_name))),
                [playlist_name] + song_name,
            )
            conn.commit()
            return cursor.rowcount
