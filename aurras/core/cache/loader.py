"""
Cache Loading Module

This module provides a class for loading data from the cache database.
"""

from aurras.core.cache import cache_db_connection


class LoadSongHistoryData:
    """
    Class for loading song history data from the cache database.
    """

    def __init__(self) -> None:
        """Initialize the cache database connection."""

    def load_song_metadata_from_db(self):
        """
        Loads basic song metadata from the cache database.

        Returns:
            list: A list of tuples containing (query, name, url)
        """
        with cache_db_connection as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT song_user_searched, track_name, url FROM cache")
            return cursor.fetchall()

    def load_song_full_metadata_from_db(self):
        """
        Loads complete song metadata from the cache database.

        Returns:
            list: A list of tuples containing complete song metadata
        """
        with cache_db_connection as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT 
                    song_user_searched, track_name, url,
                    artist_name, album_name, thumbnail_url, duration
                FROM cache"""
            )
            return cursor.fetchall()

    def load_song_with_lyrics(self, track_name=None, artist_name=None):
        """
        Loads song data including lyrics from the database.

        Args:
            track_name: Optional song name to filter by
            artist_name: Optional artist name to filter by

        Returns:
            Dictionary with song metadata and lyrics
        """
        with cache_db_connection as conn:
            cursor = conn.cursor()

            query = """
                SELECT 
                    c.id, c.track_name, c.url, 
                    c.artist_name, c.album_name, c.thumbnail_url, c.duration,
                    l.synced_lyrics, l.plain_lyrics
                FROM cache c
                LEFT JOIN lyrics l ON c.id = l.cache_id
                WHERE 1=1
            """
            params = []

            if track_name:
                query += " AND c.track_name LIKE ?"
                params.append(f"%{track_name}%")

            if artist_name:
                query += " AND c.artist_name LIKE ?"
                params.append(f"%{artist_name}%")

            cursor.execute(query, params)
            rows = cursor.fetchall()

            results = []
            for row in rows:
                results.append(
                    {
                        "id": row[0],
                        "track_name": row[1],
                        "url": row[2],
                        "artist_name": row[3],
                        "album_name": row[4],
                        "thumbnail_url": row[5],
                        "duration": row[6],
                        "synced_lyrics": row[7],
                        "plain_lyrics": row[8],
                    }
                )

            return results
