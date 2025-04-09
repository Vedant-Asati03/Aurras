"""
Lyrics cache management module.

This module provides functionality for caching lyrics in the unified database.
"""

import sqlite3
from typing import Optional, Dict, Any
from rich.console import Console

from ...utils.path_manager import PathManager

_path_manager = PathManager()
console = Console()


class LyricsCache:
    """
    LyricsCache class to manage saving and retrieving lyrics.
    Uses the unified cache database schema.
    """

    def __init__(self):
        """Initialize the lyrics cache."""
        self.cache_db_path = _path_manager.cache_db

    def load_lyrics_from_db(
        self, track_name: str, artist_name: str, album_name: str, duration: int
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve lyrics from the unified cache database.

        Args:
            track_name: Name of the track
            artist_name: Name of the artist
            album_name: Name of the album
            duration: Duration of the track in seconds

        Returns:
            Dictionary with 'synced_lyrics' and 'plain_lyrics' keys or None if not found
        """
        try:
            with sqlite3.connect(self.cache_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT l.synced_lyrics, l.plain_lyrics 
                    FROM cache c 
                    JOIN lyrics l ON c.id = l.cache_id
                    WHERE c.track_name = ? AND c.artist_name = ? AND c.album_name = ?
                    ORDER BY l.fetch_time DESC LIMIT 1
                    """,
                    (track_name, artist_name, album_name),
                )
                result = cursor.fetchone()

                if result and (result[0] or result[1]):
                    return {"synced_lyrics": result[0], "plain_lyrics": result[1]}
                return None
        except Exception as e:
            console.print(
                f"[yellow]Error retrieving lyrics from database: {e}[/yellow]"
            )
            return None

    def save_lyrics(
        self,
        track_name: str,
        artist_name: str,
        album_name: str,
        duration: int,
        synced_lyrics: list,
        plain_lyrics: list,
    ) -> None:
        """
        Save lyrics to the unified database structure.

        Args:
            track_name: Name of the track
            artist_name: Name of the artist
            album_name: Name of the album
            duration: Duration of the track in seconds
            synced_lyrics: List of synchronized lyrics lines
            plain_lyrics: List of plain lyrics lines
        """
        # Convert lyrics lists to strings
        synced_text = (
            "".join(synced_lyrics) if isinstance(synced_lyrics, list) else synced_lyrics
        )
        plain_text = (
            "".join(plain_lyrics) if isinstance(plain_lyrics, list) else plain_lyrics
        )

        try:
            # Use the unified database schema through the updater
            from ...core.cache.updater import UpdateSearchHistoryDatabase

            updater = UpdateSearchHistoryDatabase()

            # Look up song in cache by name and artist
            with sqlite3.connect(self.cache_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id FROM cache
                    WHERE track_name = ? AND artist_name = ?
                    LIMIT 1
                    """,
                    (track_name, artist_name),
                )
                result = cursor.fetchone()

                if result:
                    # Song exists in database, save lyrics
                    cache_id = result[0]
                    updater.save_lyrics(cache_id, synced_text, plain_text)
                else:
                    # Song doesn't exist, create a new entry with lyrics
                    cache_id = updater.save_to_cache(
                        f"{artist_name} - {track_name}",  # Create a search query
                        track_name,
                        "",  # No URL available
                        artist_name=artist_name,
                        album_name=album_name,
                        duration=duration,
                    )
                    if cache_id:
                        updater.save_lyrics(cache_id, synced_text, plain_text)
        except Exception as e:
            console.print(f"[yellow]Error saving lyrics to database: {e}[/yellow]")
