"""
Lyrics Handler Module

This module provides functionality for fetching, caching, and displaying lyrics.
"""

import re
import time
import random
import logging
import sqlite3
from typing import List, Dict, Any, Optional, Tuple

from ..utils.path_manager import PathManager
from ..utils.exceptions import LyricsError
from ..services.lyrics import LyricsManager

_path_manager = PathManager()
logger = logging.getLogger(__name__)


class LyricsHandler:
    """
    Handler for lyrics fetching, caching and display.

    This class provides a simplified interface for working with lyrics,
    using the unified database structure.
    """

    def __init__(self):
        """Initialize the lyrics handler."""
        self._lyrics_manager = LyricsManager()
        self._memory_cache: Dict[str, List[str]] = {}
        self._db_path = _path_manager.cache_db

    def has_lyrics_support(self) -> bool:
        """Check if lyrics support is available."""
        try:
            # Use the underlying manager to check availability
            return self._lyrics_manager._should_show_lyrics()
        except Exception as e:
            logger.error(f"Error checking lyrics support: {e}")
            return False

    def fetch_lyrics(
        self, song: str, artist: str, album: str, duration: int
    ) -> List[str]:
        """
        Fetch lyrics for a song from the lyrics service.

        Args:
            song: Song name
            artist: Artist name
            album: Album name
            duration: Song duration in seconds

        Returns:
            List of lyrics lines
        """
        try:
            # Skip if song title is missing or just "Unknown"
            if not song or song == "Unknown" or not song.strip():
                logger.warning("Cannot fetch lyrics: missing song title")
                return []

            # Log what we're searching for
            logger.info(
                f"Fetching lyrics for: Song='{song}', Artist='{artist}', Album='{album}'"
            )

            # Try to get from memory cache first
            cached_lyrics = self.get_from_cache(song, artist, album)
            if cached_lyrics:
                return cached_lyrics

            # Fetch from the lyrics service
            lyrics_data = self._lyrics_manager.obtain_lyrics_info(
                song, artist, album, duration
            )

            if lyrics_data:
                # Extract synced lyrics if available, otherwise use plain lyrics
                if lyrics_data.get("synced_lyrics"):
                    # Synced lyrics can be a string or list of lines
                    lyrics_lines = self._ensure_list(lyrics_data["synced_lyrics"])
                    if lyrics_lines:
                        logger.info(f"Found synced lyrics for '{song}'")
                        return lyrics_lines

                # Fall back to plain lyrics
                if lyrics_data.get("plain_lyrics"):
                    lyrics_lines = self._ensure_list(lyrics_data["plain_lyrics"])
                    if lyrics_lines:
                        logger.info(f"Found plain lyrics for '{song}'")
                        return lyrics_lines

            # No lyrics found
            logger.info(f"No lyrics found for '{song}'")
            return []

        except Exception as e:
            logger.error(f"Error fetching lyrics: {e}")
            raise LyricsError(f"Failed to fetch lyrics: {e}")

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
            lyrics = self._get_from_db(song, artist, album)
            if lyrics:
                # Store in memory cache for faster retrieval next time
                self._memory_cache[cache_key] = lyrics
                return lyrics
        except Exception as e:
            logger.warning(f"Error getting lyrics from database: {e}")

        return None

    def store_in_cache(
        self, lyrics: List[str], song: str, artist: str, album: str
    ) -> None:
        """
        Store lyrics in both memory cache and database.

        Args:
            lyrics: List of lyrics lines
            song: Song name
            artist: Artist name
            album: Album name
        """
        if not lyrics:
            return

        # Store in memory cache
        cache_key = self._generate_cache_key(song, artist, album)
        self._memory_cache[cache_key] = lyrics

        # Store in database cache
        try:
            synced_text = "\n".join(lyrics) if self._is_synced_lyrics(lyrics) else ""
            plain_text = (
                "\n".join(lyrics)
                if not synced_text
                else self._extract_plain_lyrics(lyrics)
            )

            # Get song_id from cache table
            with sqlite3.connect(self._db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id FROM cache
                    WHERE track_name = ? AND artist_name = ? 
                    ORDER BY fetch_time DESC LIMIT 1
                    """,
                    (song, artist),
                )
                result = cursor.fetchone()

                if result:
                    cache_id = result[0]
                    # Insert into lyrics table
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO lyrics
                        (cache_id, synced_lyrics, plain_lyrics, fetch_time)
                        VALUES (?, ?, ?, ?)
                        """,
                        (cache_id, synced_text, plain_text, int(time.time())),
                    )
                    logger.debug(f"Stored lyrics in database for '{song}'")
                else:
                    # Create new cache entry if song doesn't exist
                    cursor.execute(
                        """
                        INSERT INTO cache
                        (song_user_searched, track_name, artist_name, album_name, fetch_time)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (f"{artist} - {song}", song, artist, album, int(time.time())),
                    )
                    cache_id = cursor.lastrowid

                    # Insert lyrics
                    cursor.execute(
                        """
                        INSERT INTO lyrics
                        (cache_id, synced_lyrics, plain_lyrics, fetch_time)
                        VALUES (?, ?, ?, ?)
                        """,
                        (cache_id, synced_text, plain_text, int(time.time())),
                    )
                    logger.debug(
                        f"Created new cache entry and stored lyrics for '{song}'"
                    )
        except Exception as e:
            logger.error(f"Error storing lyrics in database: {e}")

    def create_focused_lyrics_view(
        self,
        lyrics_lines: List[str],
        current_time: float,
        song: str = "",
        artist: str = "",
        album: str = "",
        context_lines: int = 3,
    ) -> str:
        """
        Create a focused view of lyrics with the current line highlighted.

        Args:
            lyrics_lines: List of lyrics lines
            current_time: Current playback position in seconds
            song: Song name (for logging)
            artist: Artist name (for logging)
            album: Album name (for logging)
            context_lines: Number of context lines to show

        Returns:
            Formatted lyrics text with highlighting
        """
        unavailable_lyrics_messages = [
            "[bold red]No lyrics available[/bold red]",
            "[bold orange]Wow! so empty[/bold orange]",
            "[bold yellow]Seems like nothing came out[/bold yellow]",
            "[bold green]Lyrics? What lyrics?[/bold green]",
            "[bold blue]Lyrics? I don't see any lyrics[/bold blue]",
            "[bold magenta]Lyrics? What are those?[/bold magenta]",
            "[bold cyan]Lyrics? I don't think so[/bold cyan]",
            "[bold white]Lyrics? Not today[/bold white]",
            "[bold pink]Uh-oh! No lyrics here[/bold pink]",
            "[bold purple]No luck today, huh?[/bold purple]",
        ]
        if not lyrics_lines:
            return random.choice(unavailable_lyrics_messages)

        # Check if these are synced lyrics by looking for timestamp patterns
        if not self._is_synced_lyrics(lyrics_lines):
            # For unsynced lyrics, just show them as is
            return "\n".join(f"[dim]{line}[/dim]" for line in lyrics_lines[:10])

        # Parse timestamps and build a list of (timestamp, text) tuples
        parsed_lyrics = []
        timestamp_pattern = r"\[(\d+):(\d+\.\d+)\](.*?)(?=\[\d+:\d+\.\d+\]|$)"

        # First, collect all timestamp-text pairs from all lines
        for line in lyrics_lines:
            matches = re.finditer(timestamp_pattern, line)
            for match in matches:
                minutes = int(match.group(1))
                seconds = float(match.group(2))
                timestamp = minutes * 60 + seconds
                text = match.group(3).strip()
                if text:  # Only add if there's actual text
                    parsed_lyrics.append((timestamp, text))

        # Sort by timestamp in case they're not in order
        parsed_lyrics.sort(key=lambda x: x[0])

        if not parsed_lyrics:
            return "[italic]Could not parse lyrics timestamps[/italic]"

        # Find the current line based on timestamp
        current_index = 0
        for i, (timestamp, _) in enumerate(parsed_lyrics):
            if timestamp > current_time:
                break
            current_index = i

        # Calculate the range of lines to display
        start_index = max(0, current_index - context_lines)
        end_index = min(len(parsed_lyrics), current_index + context_lines + 1)

        # Build the focused lyrics display with highlighting
        result_lines = []

        # Add a header showing current position if we're not at the beginning
        if start_index > 0:
            result_lines.append("[dim]...[/dim]")

        # Add the lines with appropriate highlighting, but without timestamps
        for i in range(start_index, end_index):
            _, text = parsed_lyrics[i]

            if i == current_index:
                # Current line - highlight with bold green
                result_lines.append(f"[bold green]{text}[/bold green]")
            else:
                # Other lines - dim text for better contrast
                result_lines.append(f"[dim]{text}[/dim]")

        # Add a footer if we're not at the end
        if end_index < len(parsed_lyrics):
            result_lines.append("[dim]...[/dim]")

        return "\n".join(result_lines)

    # --- Helper Methods ---

    def _get_from_db(self, song: str, artist: str, album: str) -> Optional[List[str]]:
        """
        Try to get lyrics from database cache.

        Args:
            song: Song name
            artist: Artist name
            album: Album name

        Returns:
            Cached lyrics if found, None otherwise
        """
        try:
            # Skip lookup if missing essential data
            if not song or song == "Unknown" or not song.strip():
                return None

            logger.debug(
                f"DB lookup: Song='{song}', Artist='{artist}', Album='{album}'"
            )

            with sqlite3.connect(self._db_path) as conn:
                cursor = conn.cursor()

                # Try exact match first
                cursor.execute(
                    """
                    SELECT l.synced_lyrics, l.plain_lyrics 
                    FROM cache c 
                    JOIN lyrics l ON c.id = l.cache_id
                    WHERE c.track_name = ? AND c.artist_name = ?
                    LIMIT 1
                    """,
                    (song, artist),
                )
                result = cursor.fetchone()

                if result and (result[0] or result[1]):
                    return (
                        result[0].splitlines() if result[0] else result[1].splitlines()
                    )

                # Try fuzzy match if exact match fails and we have a reasonable song name
                if len(song) > 3:  # Only try fuzzy match for substantial titles
                    cursor.execute(
                        """
                        SELECT l.synced_lyrics, l.plain_lyrics 
                        FROM cache c 
                        JOIN lyrics l ON c.id = l.cache_id
                        WHERE c.track_name LIKE ?
                        LIMIT 1
                        """,
                        (f"%{song}%",),
                    )
                    result = cursor.fetchone()

                    if result and (result[0] or result[1]):
                        synced_lyrics, plain_lyrics = result

                        # Prefer synced lyrics if available
                        if synced_lyrics:
                            logger.debug(
                                f"Found synced lyrics in DB with fuzzy match for '{song}'"
                            )
                            return synced_lyrics.splitlines()
                        elif plain_lyrics:
                            logger.debug(
                                f"Found plain lyrics in DB with fuzzy match for '{song}'"
                            )
                            return plain_lyrics.splitlines()

                logger.debug(f"No lyrics found in DB for '{song}'")
                return None

        except Exception as e:
            logger.error(f"Error retrieving lyrics from DB: {e}")
            return None

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
    def _extract_plain_lyrics(lyrics: List[str]) -> str:
        """
        Extract plain text from synced lyrics.

        Args:
            lyrics: Synced lyrics lines

        Returns:
            Plain lyrics text
        """
        plain_lines = []
        for line in lyrics:
            # Remove timestamp patterns
            plain_line = re.sub(r"\[\d+:\d+\.\d+\]", "", line).strip()
            if plain_line:
                plain_lines.append(plain_line)
        return "\n".join(plain_lines)
