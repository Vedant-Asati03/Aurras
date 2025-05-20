"""
Lyrics cache management module.

This module provides functionality for caching lyrics in memory and database.
"""

import re
import sqlite3
from typing import Optional, Dict, List, Any

from aurras.utils.logger import get_logger
from aurras.utils.path_manager import _path_manager
from aurras.core.cache.updater import UpdateSearchHistoryDatabase

logger = get_logger("aurras.services.lyrics.cache", log_to_console=False)


class LyricsCache:
    """
    LyricsCache class to manage saving and retrieving lyrics.

    Handles both memory caching and persistent database storage
    using the unified cache database schema.
    """

    def __init__(self):
        """Initialize the lyrics cache."""
        self.cache_db_path = _path_manager.cache_db
        self._memory_cache: Dict[str, List[str]] = {}

    def get_from_cache(self, song: str, artist: str, album: str) -> Optional[List[str]]:
        """
        Try to get lyrics from cache (memory or database).

        Args:
            song: Song name
            artist: Artist name
            album: Album name

        Returns:
            Cached lyrics if found, None otherwise
        """
        # First try memory cache (faster)
        cache_key = self._generate_cache_key(song, artist, album)
        if cache_key in self._memory_cache:
            logger.debug(f"Found lyrics in memory cache for '{song}'")
            return self._memory_cache[cache_key]

        # Then try database cache
        try:
            cached_lyrics = self.load_lyrics_from_db(song, artist, album)

            if cached_lyrics:
                synced_lyrics = cached_lyrics.get("synced_lyrics", "")
                plain_lyrics = cached_lyrics.get("plain_lyrics", "")

                # Choose the most appropriate format
                lyrics = None
                if synced_lyrics:
                    lyrics = self._ensure_list(synced_lyrics)
                elif plain_lyrics:
                    lyrics = self._ensure_list(plain_lyrics)

                if lyrics:
                    # Store in memory cache for faster retrieval next time
                    self._memory_cache[cache_key] = lyrics
                    return lyrics
        except Exception as e:
            logger.warning(f"Error getting lyrics from database: {e}")

        return None

    def store_in_cache(
        self, lyrics: List[str], song: str, artist: str, album: str, duration: int = 0
    ) -> None:
        """
        Store lyrics in both memory cache and database.

        Args:
            lyrics: List of lyrics lines
            song: Song name
            artist: Artist name
            album: Album name
            duration: Song duration (optional)
        """
        if not lyrics:
            return

        # Store in memory cache
        cache_key = self._generate_cache_key(song, artist, album)
        self._memory_cache[cache_key] = lyrics

        # Determine if these are synced lyrics
        is_synced = self._is_synced_lyrics(lyrics)

        # Prepare lyrics for database storage
        synced_lyrics = []
        plain_lyrics = []

        if is_synced:
            synced_lyrics = lyrics
            plain_lyrics = self._extract_plain_lyrics(lyrics)
        else:
            plain_lyrics = lyrics

        # Store in database
        try:
            self._save_lyrics(
                song, artist, album, duration, synced_lyrics, plain_lyrics
            )
            logger.debug(f"Stored lyrics in database for '{song}'")
        except Exception as e:
            logger.error(f"Error storing lyrics in database: {e}")

    def load_lyrics_from_db(
        self, track_name: str, artist_name: str, album_name: str
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
            # Skip lookup if missing essential data
            if not track_name or track_name == "Unknown" or not track_name.strip():
                return None

            logger.debug(
                f"DB lookup: Song='{track_name}', Artist='{artist_name}', Album='{album_name}'"
            )

            with sqlite3.connect(self.cache_db_path) as conn:
                cursor = conn.cursor()

                # Try exact match first
                cursor.execute(
                    """
                    SELECT l.synced_lyrics, l.plain_lyrics 
                    FROM cache c 
                    JOIN lyrics l ON c.id = l.cache_id
                    WHERE c.track_name = ? AND c.artist_name = ?
                    ORDER BY l.fetch_time DESC LIMIT 1
                    """,
                    (track_name, artist_name),
                )
                result = cursor.fetchone()

                if result and (result[0] or result[1]):
                    synced_lyrics, plain_lyrics = result
                    # For synced lyrics, ensure we properly preserve exact line breaks
                    return {
                        "synced_lyrics": synced_lyrics,
                        "plain_lyrics": plain_lyrics,
                    }

                # Try fuzzy match if exact match fails and we have a reasonable track name
                if len(track_name) > 3:  # Only try fuzzy match for substantial titles
                    cursor.execute(
                        """
                        SELECT l.synced_lyrics, l.plain_lyrics 
                        FROM cache c 
                        JOIN lyrics l ON c.id = l.cache_id
                        WHERE c.track_name LIKE ?
                        ORDER BY l.fetch_time DESC LIMIT 1
                        """,
                        (f"%{track_name}%",),
                    )
                    result = cursor.fetchone()

                    if result and (result[0] or result[1]):
                        synced_lyrics, plain_lyrics = result
                        return {
                            "synced_lyrics": synced_lyrics,
                            "plain_lyrics": plain_lyrics,
                        }

                logger.debug(f"No lyrics found in DB for '{track_name}'")
                return None

        except Exception as e:
            logger.error(f"Error retrieving lyrics from DB: {e}")
            return None

    def _save_lyrics(
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
            "\n".join(synced_lyrics)
            if isinstance(synced_lyrics, list)
            else synced_lyrics
        )
        plain_text = (
            "\n".join(plain_lyrics) if isinstance(plain_lyrics, list) else plain_lyrics
        )

        try:
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
            logger.error(f"Error saving lyrics to database: {e}")

    def _generate_cache_key(self, song: str, artist: str, album: str) -> str:
        """
        Generate a cache key for lyrics.

        Args:
            song: Song name
            artist: Artist name
            album: Album name

        Returns:
            Cache key string
        """
        # Normalize and combine fields for a unique key
        return "_".join(
            [
                self._normalize_str(song),
                self._normalize_str(artist),
                self._normalize_str(album),
            ]
        )

    @staticmethod
    def _normalize_str(s: Optional[str]) -> str:
        """
        Normalize a string for more reliable cache lookups.

        Args:
            s: String to normalize

        Returns:
            Normalized string
        """
        if not s or s == "Unknown":
            return ""
        return s.lower().strip()

    @staticmethod
    def _ensure_list(lyrics: Any) -> List[str]:
        """
        Ensure lyrics are in list format.

        Args:
            lyrics: Lyrics in string or list format

        Returns:
            List of lyrics lines
        """
        if isinstance(lyrics, str):
            return lyrics.splitlines()
        elif isinstance(lyrics, list):
            return lyrics
        return []

    @staticmethod
    def _is_synced_lyrics(lyrics: List[str]) -> bool:
        """
        Check if lyrics are synced (contain timestamps).

        Args:
            lyrics: Lyrics lines to check

        Returns:
            True if lyrics appear to be synced
        """
        # Check a few lines for timestamp patterns
        timestamp_pattern = r"\[\d+:\d+\.\d+\]"
        for line in lyrics[:10]:  # Check first 10 lines
            if re.search(timestamp_pattern, line):
                return True
        return False

    @staticmethod
    def _extract_plain_lyrics(lyrics: List[str]) -> List[str]:
        """
        Extract plain text from synced lyrics.

        Args:
            lyrics: Synced lyrics lines

        Returns:
            Plain lyrics without timestamps
        """
        plain_lines = []
        for line in lyrics:
            # Remove timestamp patterns
            plain_line = re.sub(r"\[\d+:\d+\.\d+\]", "", line).strip()
            if plain_line:
                plain_lines.append(plain_line)
        return plain_lines
