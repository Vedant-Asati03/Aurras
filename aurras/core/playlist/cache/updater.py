"""
Cache Update Module

This module provides a class for updating the playlist database.
"""

import time
from typing import List

from aurras.utils.console import console
from aurras.utils.logger import get_logger
from aurras.core.playlist.cache import playlist_db_connection

logger = get_logger("aurras.core.playlist.cache.updater", log_to_console=False)


class UpdatePlaylistDatabase:
    """
    Class for updating the playlist database.
    """

    def __init__(self) -> None:
        """Initialize the playlist database if needed."""

    def save_playlist(
        self,
        playlist_name: str,
        description: str = "",
        updated_at: int = 0,
        is_downloaded: bool = False,
    ) -> None:
        """
        Saves or updates a playlist. If it already exists (by name), updates it.
        """
        with playlist_db_connection as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO playlists (name, description, updated_at, is_downloaded)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    description = excluded.description,
                    updated_at = excluded.updated_at,
                    is_downloaded = excluded.is_downloaded
                """,
                (playlist_name, description, updated_at, is_downloaded),
            )
            conn.commit()

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
            songs_metadata (List[tuple]): List of tuples containing song metadata
                (playlist_id, track_name, artist_name, album_name, added_at)
        """
        with playlist_db_connection as conn:
            cursor = conn.cursor()
            cursor.executemany(
                """
                INSERT INTO playlist_songs 
                (playlist_id, track_name, artist_name, added_at)
                VALUES (?, ?, ?, ?)
                """,
                songs_metadata,
            )
            conn.commit()

    def batch_save_songs_to_playlist(
        self, playlist_name: str, songs_metadata: List[tuple]
    ) -> None:
        """
        Save multiple songs to a playlist in a batch operation.

        Args:
            playlist_name (str): The name of the playlist to add songs to
            songs_metadata (List[tuple]): List of tuples containing song metadata
                (playlist_id, track_name, artist_name, added_at)
        """
        current_time = int(time.time())

        self.save_playlist(
            playlist_name=playlist_name,
            description=f"Playlist {playlist_name}",
            updated_at=current_time,
            is_downloaded=True,
        )

        playlist_id = self._get_playlist_id(playlist_name)
        if playlist_id is None:
            raise ValueError(f"Playlist '{playlist_name}' not found in the database.")

        playlist_songs_metadata_batch: List[tuple] = [
            (
                playlist_id,
                data[0],  # track_name
                data[1],  # artist_name
                data[4],  # added_at - same timestamp for batch
            )
            for data in songs_metadata
        ]

        self.save_song_to_playlist(playlist_songs_metadata_batch)

    def remove_playlist(self, playlist_names: List[str]) -> int:
        """
        Removes playlists from the database.

        Args:
            playlist_names (List[str]): List of playlist names to be removed

        Returns:
            int: Number of playlists actually deleted

        Raises:
            ValueError: If playlist_names is empty
            DatabaseError: If a database operation fails
        """
        if not playlist_names:
            raise ValueError("No playlist names provided for deletion")

        # Validate that playlists exist before deletion
        existing_playlists = []
        non_existing_playlists = []

        try:
            with playlist_db_connection as conn:
                cursor = conn.cursor()

                # Check which playlists actually exist
                for playlist_name in playlist_names:
                    cursor.execute(
                        "SELECT name FROM playlists WHERE name = ?", (playlist_name,)
                    )
                    if cursor.fetchone():
                        existing_playlists.append(playlist_name)
                    else:
                        non_existing_playlists.append(playlist_name)

                if non_existing_playlists:
                    console.print_warning(
                        f"Warning: The following playlists don't exist: {', '.join(non_existing_playlists)}"
                    )

                if not existing_playlists:
                    console.print_warning("No valid playlists found to delete")
                    return 0

                # First, delete associated songs (manual cascade due to SQLite limitations)
                cursor.execute(
                    """
                    DELETE FROM playlist_songs 
                    WHERE playlist_id IN (
                        SELECT id FROM playlists WHERE name IN ({})
                    )
                    """.format(",".join("?" * len(existing_playlists))),
                    existing_playlists,
                )

                # Then delete the playlists
                cursor.execute(
                    """
                    DELETE FROM playlists 
                    WHERE name IN ({})
                    """.format(",".join("?" * len(existing_playlists))),
                    existing_playlists,
                )
                playlists_deleted = cursor.rowcount

                conn.commit()

                if playlists_deleted > 0:
                    console.print_success(
                        f"Successfully deleted {playlists_deleted} playlist(s)"
                    )

                return playlists_deleted

        except Exception as e:
            logger.error(f"Error removing playlists: {e}", exc_info=True)
            console.print_error(f"Error: Failed to remove playlists: {str(e)}")
            raise

    def remove_song_from_playlist(
        self, playlist_name: str, song_name: List[str]
    ) -> None:
        """
        Removes a song from a specific playlist.

        Args:
            playlist_name (str): The name of the playlist
            song_name (List[str]): List of song names to be removed
        """
        with playlist_db_connection as conn:
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
