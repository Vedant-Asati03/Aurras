"""
Cache Loading Module

This module provides a class for loading data from the playlist database.
"""

from typing import List, Dict, Any, Optional

from aurras.core.playlist.cache import playlist_db_connection


class LoadPlaylistData:
    """
    Class for loading playlist data from the database.
    """

    def __init__(self) -> None:
        """Initialize the playlist database if needed."""

    def _get_playlist_id(self, playlist_name: str) -> int:
        """
        Retrieves the ID of a playlist by its name.

        Args:
            playlist_name (str): The name of the playlist

        Returns:
            int: The ID of the playlist
        """
        with playlist_db_connection as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT id FROM playlists WHERE name = ?""",
                (playlist_name,),
            )
            return cursor.fetchone()[0]

    def load_playlists_with_partial_data(self) -> Optional[List[Dict[str, Any]]]:
        """
        Loads all playlists from the database with their metadata.

        This includes the playlist ID, name, description, last updated time, and is_downloaded.

        Returns:
            list: A list of dictionaries containing playlist metadata
        """
        with playlist_db_connection as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM playlists")

            data = [
                {
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "updated_at": row[3],
                    "is_downloaded": row[4],
                }
                for row in cursor.fetchall()
            ]

            if not data:
                return []

            return data

    def load_playlists_with_complete_data(self) -> List[Dict[str, Any]]:
        """
        Loads all playlists from the database with their metadata and songs.

        This includes the playlist ID, name, description, updated_at, is_downloaded, and a list of songs in each playlist.
        Each song includes its track name, artist name, album name, and added_at.

        Returns:
            list: A list of dictionaries containing playlist metadata and songs
        """
        playlists_metadata = self.load_playlists_with_partial_data()

        for playlist in playlists_metadata:
            playlist["songs"] = self.load_playlist_songs_with_full_metadata(
                playlist["name"]
            )

        return playlists_metadata

    def load_playlist_songs_with_full_metadata(
        self, playlist_name: str
    ) -> List[Dict[str, Any]]:
        """
        Loads songs from a specific playlist.

        Args:
            playlist_name (str): The name of the playlist.

        Returns:
            list: A list of dictionaries containing song metadata
        """
        playlist_id = self._get_playlist_id(playlist_name)

        with playlist_db_connection as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM playlist_songs WHERE playlist_id = ?""", (playlist_id,)
            )
            data = [
                {
                    "id": row[0],
                    "playlist_id": row[1],
                    "track_name": row[2],
                    "artist_name": row[3],
                    "album_name": row[4],
                    "added_at": row[5],
                }
                for row in cursor.fetchall()
            ]

            if not data:
                return []

            return data
