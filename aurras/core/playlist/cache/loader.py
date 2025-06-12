"""
Cache Loading Module

This module provides a class for loading data from the playlist database.
"""

from typing import List, Dict, Any, Optional

from aurras.utils.handle_fuzzy_search import FuzzySearcher
from aurras.core.playlist.cache import playlist_db_connection


class LoadPlaylistData:
    """
    Class for loading playlist data from the database.
    """

    def __init__(self) -> None:
        """Initialize the playlist database if needed."""
        self.fuzzy_search = FuzzySearcher(threshold=0.88)

    def _get_playlist_id(self, playlist_name: str) -> int | None:
        """
        Retrieves the playlist ID and corrected name using fuzzy matching in a single database query.

        Args:
            playlist_name (str): Name of the playlist to find

        Returns:
            tuple[int, str] | None: A tuple of (playlist_id, corrected_name) if found, None otherwise
        """
        with playlist_db_connection as conn:
            cursor = conn.cursor()
            cursor.execute("""SELECT id, name FROM playlists""")
            playlists_data = cursor.fetchall()

        playlist_names = [row[1] for row in playlists_data]

        if corrected_playlist_name := self.fuzzy_search.find_best_match(
            playlist_name, playlist_names
        ):
            id = [row[0] for row in playlists_data if row[1] == corrected_playlist_name]
            return id[0]

        return None

    def retrieve_playlist_info(
        self, playlist_name: str = None
    ) -> List[Dict[str, Any]] | None:
        """
        Loads all playlists from the database with their metadata.

        This includes the playlist ID, name, description, last updated time, and is_downloaded.

        Returns:
            list: A list of dictionaries containing playlist metadata
        """
        if playlist_name:
            playlist_id = self._get_playlist_id(playlist_name)

            if playlist_id is None:
                return None

            with playlist_db_connection as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """SELECT * FROM playlists WHERE id = ?""",
                    (playlist_id,),
                )

                data = cursor.fetchone()

                if not data:
                    return None

                return [
                    {
                        "id": data[0],
                        "name": data[1],
                        "description": data[2],
                        "updated_at": data[3],
                        "is_downloaded": data[4],
                    }
                ]

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

    def _get_playlist_content(
        self, playlist_ids: List[int]
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieves the content of a playlist by its ID.

        Args:
            playlist_id (list): List of playlist IDs

        Returns:
            list: A list of dictionaries containing song metadata
        """
        with playlist_db_connection as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM playlist_songs WHERE playlist_id IN ({})""".format(
                    ",".join("?" * len(playlist_ids))
                ),
                playlist_ids,
            )

            data = [
                {
                    "id": row[0],
                    "playlist_id": row[1],
                    "track_name": row[2],
                    "artist_name": row[3],
                    "added_at": row[4],
                }
                for row in cursor.fetchall()
            ]

            if not data:
                return []

            return data

    def retireve_playlist_info_with_content(
        self, playlist_name: str = None
    ) -> List[Dict[str, Any]]:
        """
        Loads songs from a specific playlist.

        Args:
            playlist_name (str): The name of the playlist.

        Returns:
            list: A list of dictionaries containing song metadata
        """
        playlists_id: List[int] = []
        playlists_metadata = self.retrieve_playlist_info()

        if playlist_name:
            playlist_id = self._get_playlist_id(playlist_name)
            if playlist_id is None:
                return []

            playlists_id.append(playlist_id)
        else:
            playlists_id.extend([playlist["id"] for playlist in playlists_metadata])

        data = self._get_playlist_content(playlists_id)

        if not data:
            return []

        return data
