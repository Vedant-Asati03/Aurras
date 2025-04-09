"""
Lyrics Handler Module

This module provides functionality for fetching, caching, and displaying lyrics.
"""

import re
import time
import random
import logging
import sqlite3
from typing import List, Dict, Any, Optional, Tuple, Union, Callable

from ..utils.path_manager import PathManager
from ..utils.exceptions import LyricsError
from ..services.lyrics import LyricsManager
from ..utils.console_manager import get_console, get_available_themes, get_current_theme
from ..utils.gradient_utils import get_gradient_style, apply_gradient_to_text

_path_manager = PathManager()
logger = logging.getLogger(__name__)

# Regular expression patterns as constants for better maintainability
TIMESTAMP_PATTERN = r"\[(\d+):(\d+\.\d+)\]"
WORD_TIMESTAMP_PATTERN = r"<\d+:\d+\.\d+>"
LINE_TIMESTAMP_PATTERN = r"\[\d+:\d+\.\d+\]"
WORD_PATTERN = r"<(\d+):(\d+\.\d+)>\s*([^<]+)"
LINE_PATTERN = r"\[(\d+):(\d+\.\d+)\](.*?)(?=\[\d+:\d+\.\d+\]|$)"


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
        self._console = get_console()
        # Optional simple gradient view method for subclasses to implement
        self._create_simple_gradient_view: Callable[[List[str]], str] = (
            lambda x: "\n".join(x)
        )

    def has_lyrics_support(self) -> bool:
        """Check if lyrics support is available."""
        try:
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

            # Try to get from memory cache first
            cached_lyrics = self.get_from_cache(song, artist, album)
            if cached_lyrics:
                return cached_lyrics

            # Log what we're searching for
            logger.info(
                f"Fetching lyrics for: Song='{song}', Artist='{artist}', Album='{album}'"
            )

            # Fetch from the lyrics service
            lyrics_data = self._lyrics_manager.obtain_lyrics_info(
                song, artist, album, duration
            )

            if not lyrics_data:
                logger.info(f"No lyrics found for '{song}'")
                return []

            # Extract synced lyrics if available, otherwise use plain lyrics
            if synced_lyrics := lyrics_data.get("synced_lyrics"):
                lyrics_lines = self._ensure_list(synced_lyrics)
                if lyrics_lines:
                    logger.info(f"Found synced lyrics for '{song}'")
                    return lyrics_lines

            # Fall back to plain lyrics
            if plain_lyrics := lyrics_data.get("plain_lyrics"):
                lyrics_lines = self._ensure_list(plain_lyrics)
                if lyrics_lines:
                    logger.info(f"Found plain lyrics for '{song}'")
                    return lyrics_lines

            # No usable lyrics found
            logger.info(f"No usable lyrics found for '{song}'")
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

    def get_no_lyrics_message(self) -> str:
        """
        Get a themed "no lyrics available" message.

        Returns:
            A formatted message indicating no lyrics are available
        """
        # Get theme color with safe fallbacks
        theme_style = get_gradient_style()
        theme_color = self._get_theme_color(theme_style)

        # List of fun messages
        unavailable_lyrics_messages = [
            f"[bold {theme_color}]No lyrics available[/bold {theme_color}]",
            f"[bold {theme_color}]Wow! so empty[/bold {theme_color}]",
            f"[bold {theme_color}]Seems like nothing came out[/bold {theme_color}]",
            f"[bold {theme_color}]Lyrics? What lyrics?[/bold {theme_color}]",
            f"[bold {theme_color}]Lyrics? I don't see any lyrics[/bold {theme_color}]",
            f"[bold {theme_color}]Lyrics? What are those?[/bold {theme_color}]",
            f"[bold {theme_color}]Lyrics? I don't think so[/bold {theme_color}]",
            f"[bold {theme_color}]Lyrics? Not today[/bold {theme_color}]",
            f"[bold {theme_color}]Uh-oh! No lyrics here[/bold {theme_color}]",
            f"[bold {theme_color}]No luck today, huh?[/bold {theme_color}]",
        ]

        return random.choice(unavailable_lyrics_messages)

    def get_waiting_message(self) -> str:
        """
        Get a themed "waiting for lyrics" message.

        Returns:
            A formatted message indicating lyrics are being fetched
        """
        theme_style = get_gradient_style()
        theme_color = self._get_theme_color(theme_style)
        return f"[italic {theme_color}]Fetching lyrics[/italic {theme_color}]"

    def get_error_message(self, error_text: str) -> str:
        """
        Get a themed error message.

        Args:
            error_text: The error text to display

        Returns:
            A formatted error message
        """
        # Use feedback colors for consistency with user feedback
        error_text = apply_gradient_to_text(f"Error: {error_text}", "feedback")
        return f"[italic]{error_text}[/italic]"

    def create_focused_lyrics_view(
        self,
        lyrics_lines: List[str],
        current_time: float,
        song: str = "",
        artist: str = "",
        album: str = "",
        context_lines: int = 6,
        plain_mode: bool = False,
    ) -> str:
        """
        Create a focused view of lyrics with the current line highlighted with gradient effect.

        Args:
            lyrics_lines: List of lyrics lines
            current_time: Current playback position in seconds
            song: Song name (for logging)
            artist: Artist name (for logging)
            album: Album name
            context_lines: Number of context lines to show
            plain_mode: If True, display plain lyrics without timestamps

        Returns:
            Formatted lyrics text with gradient highlighting
        """
        if not lyrics_lines:
            return self.get_no_lyrics_message()

        # Different display modes based on lyrics type and requested mode
        if plain_mode:
            return self._display_plain_lyrics(lyrics_lines)
        # elif self._is_enhanced_lrc(lyrics_lines):
        #     return self._create_enhanced_lrc_view(
        #         lyrics_lines, current_time, context_lines
        #     )
        elif not self._is_synced_lyrics(lyrics_lines):
            return self._display_plain_lyrics(lyrics_lines)
        else:
            return self._display_synced_lyrics(
                lyrics_lines, current_time, context_lines
            )

    def _display_plain_lyrics(self, lyrics_lines: List[str]) -> str:
        """Display plain lyrics with simple gradient formatting."""
        plain_lyrics = self._get_plain_lyrics(lyrics_lines)
        return self._create_simple_gradient_view(plain_lyrics[:15])

    def _display_synced_lyrics(
        self, lyrics_lines: List[str], current_time: float, context_lines: int
    ) -> str:
        """Display synced lyrics with the current line highlighted."""
        # Parse timestamps and build a list of (timestamp, text) tuples
        parsed_lyrics = self._parse_synced_lyrics(lyrics_lines)

        if not parsed_lyrics:
            return "[italic]Could not parse lyrics timestamps[/italic]"

        # Find the current line based on timestamp
        current_index = self._find_current_lyric_index(parsed_lyrics, current_time)

        # Create gradient display
        return self._create_gradient_lyrics_view(
            parsed_lyrics, current_time, current_index, context_lines
        )

    def _parse_synced_lyrics(self, lyrics_lines: List[str]) -> List[Tuple[float, str]]:
        """Parse synced lyrics into a list of (timestamp, text) tuples."""
        parsed_lyrics = []

        # First, collect all timestamp-text pairs from all lines
        for line in lyrics_lines:
            matches = re.finditer(LINE_PATTERN, line)
            for match in matches:
                minutes = int(match.group(1))
                seconds = float(match.group(2))
                timestamp = minutes * 60 + seconds
                text = match.group(3).strip()
                if text:  # Only add if there's actual text
                    parsed_lyrics.append((timestamp, text))

        # Sort by timestamp in case they're not in order
        parsed_lyrics.sort(key=lambda x: x[0])
        return parsed_lyrics

    def _find_current_lyric_index(
        self, parsed_lyrics: List[Tuple[float, str]], current_time: float
    ) -> int:
        """Find the index of the current lyric based on playback time."""
        for i, (timestamp, _) in enumerate(parsed_lyrics):
            if timestamp > current_time:
                return max(0, i - 1)
        # If we get here, we're at the last line
        return len(parsed_lyrics) - 1

    def _create_gradient_lyrics_view(
        self,
        parsed_lyrics: List[Tuple[float, str]],
        current_time: float,
        current_index: int,
        context_lines: int,
    ) -> str:
        """
        Create a themed display for synced lyrics with word-level highlighting.

        Args:
            parsed_lyrics: List of (timestamp, text) tuples
            current_time: Current playback position in seconds
            current_index: Index of current line
            context_lines: Number of context lines to show

        Returns:
            Formatted lyrics with word-level highlighting
        """
        # Calculate the range of lines to display
        start_index = max(0, current_index - context_lines)
        end_index = min(len(parsed_lyrics), current_index + context_lines + 1)

        # Get the appropriate theme colors based on the current theme
        theme_style = self._get_theme_gradient_style()

        # Build the focused lyrics display
        result_lines = []

        # Add a header showing current position if we're not at the beginning
        if start_index > 0:
            result_lines.append(f"[{theme_style['dim']}][/{theme_style['dim']}]")

        # Add the lines with proper highlighting
        for i in range(start_index, end_index):
            timestamp, text = parsed_lyrics[i]

            if i == current_index:
                # Current line - highlight with word-level animation
                word_highlight = self._simulate_word_highlighting(
                    text, timestamp, current_time, parsed_lyrics, i, theme_style
                )
                result_lines.append(word_highlight)
            else:
                # Other lines - use theme color but dimmed
                result_lines.append(
                    f"[{theme_style['dim']}]{text}[/{theme_style['dim']}]"
                )

        # Add a footer if we're not at the end
        if end_index < len(parsed_lyrics):
            result_lines.append(f"[{theme_style['dim']}][/{theme_style['dim']}]")

        return "\n".join(result_lines)

    def _simulate_word_highlighting(
        self,
        text: str,
        line_start_time: float,
        current_time: float,
        parsed_lyrics: List[Tuple[float, str]],
        line_index: int,
        theme_style: Dict[str, Any],
    ) -> str:
        """
        Simulate word-level highlighting for standard LRC format.

        Args:
            text: The line text
            line_start_time: Timestamp of current line
            current_time: Current playback position
            parsed_lyrics: All parsed lyrics
            line_index: Current line index
            theme_style: Theme style dictionary

        Returns:
            Formatted text with simulated word-level highlighting
        """
        # Split the line into words
        words = text.split()
        if not words:
            return text

        # Calculate the end time of this line (start of next line or estimate)
        line_end_time = None
        if line_index < len(parsed_lyrics) - 1:
            line_end_time = parsed_lyrics[line_index + 1][0]
        else:
            # For the last line, estimate duration based on average line duration
            if line_index > 0:
                prev_duration = line_start_time - parsed_lyrics[line_index - 1][0]
                line_end_time = line_start_time + prev_duration
            else:
                # Default to 5 seconds if we can't estimate
                line_end_time = line_start_time + 5

        # Calculate line duration
        line_duration = line_end_time - line_start_time

        # Time elapsed since start of the line
        elapsed_in_line = current_time - line_start_time

        # If elapsed time is negative, we're still before this line starts
        if elapsed_in_line < 0:
            return f"[{theme_style['dim']}]{text}[/{theme_style['dim']}]"

        # Calculate which word should be highlighted based on elapsed time percentage
        total_chars = (
            sum(len(word) for word in words) + len(words) - 1
        )  # Include spaces

        # Calculate "progress" through the line (0.0 to 1.0)
        progress = min(1.0, elapsed_in_line / line_duration)

        # Calculate which character we're at based on progress
        target_char_pos = int(progress * total_chars)

        # Figure out which word this corresponds to
        current_word_index = 0
        char_count = 0

        for i, word in enumerate(words):
            char_count += len(word)
            if i < len(words) - 1:
                char_count += 1  # Account for space
            if char_count > target_char_pos:
                current_word_index = i
                break

        # Use our existing word highlighting function with the theme style
        return self._highlight_current_word(
            [{"text": word} for word in words], current_word_index, theme_style
        )

    def _get_theme_gradient_style(self) -> Dict[str, Any]:
        """Get the gradient style based on the current theme."""
        # Get gradient styles from the shared utility
        return get_gradient_style()

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
                    # For synced lyrics, ensure we properly preserve exact line breaks
                    # by using splitlines(True) which keeps the line endings
                    if result[0]:
                        synced_lyrics = result[0].splitlines(True)
                        # Remove any trailing whitespace while preserving the timestamp format
                        synced_lyrics = [
                            line.rstrip() + "\n" if not line.endswith("\n") else line
                            for line in synced_lyrics
                        ]
                        logger.debug(f"Found synced lyrics in DB for '{song}'")
                        return synced_lyrics
                    else:
                        return result[1].splitlines()

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

                        # Prefer synced lyrics if available, with proper format preservation
                        if synced_lyrics:
                            synced_lines = synced_lyrics.splitlines(True)
                            # Ensure proper line endings
                            synced_lines = [
                                line.rstrip() + "\n"
                                if not line.endswith("\n")
                                else line
                                for line in synced_lines
                            ]
                            logger.debug(
                                f"Found synced lyrics in DB with fuzzy match for '{song}'"
                            )
                            return synced_lines
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
    def _is_enhanced_lrc(lyrics_lines: List[str]) -> bool:
        """
        Check if lyrics are in enhanced LRC format with word-level timestamps.

        Args:
            lyrics_lines: Lyrics lines to check

        Returns:
            True if lyrics are in enhanced LRC format
        """
        # Enhanced LRC detection sometimes fails on cached lyrics, let's make it more robust
        # Check for word-level timestamp pattern <MM:SS.SS>
        word_timestamp_pattern = r"<\d+:\d+\.\d+>"

        # Join all lines to check for word timestamps anywhere
        all_text = "\n".join(lyrics_lines)
        if re.search(r"\[\d+:\d+\.\d+\]", all_text) and re.search(
            word_timestamp_pattern, all_text
        ):
            # We found both line timestamps and word timestamps somewhere
            word_timestamps = re.findall(word_timestamp_pattern, all_text)
            if len(word_timestamps) >= 2:  # At least two word timestamps
                return True

        # Original line-by-line check as backup
        for line in lyrics_lines[:10]:  # Check first 10 lines
            if re.search(r"\[\d+:\d+\.\d+\]", line) and re.search(
                word_timestamp_pattern, line
            ):
                word_timestamps = re.findall(word_timestamp_pattern, line)
                if len(word_timestamps) >= 2:
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

    # def _is_enhanced_lrc(self, lyrics_lines: List[str]) -> bool:
    #     """
    #     Check if lyrics are in enhanced LRC format with word-level timestamps.

    #     Args:
    #         lyrics_lines: Lyrics lines to check

    #     Returns:
    #         True if lyrics are in enhanced LRC format
    #     """
    #     # Enhanced LRC detection sometimes fails on cached lyrics, let's make it more robust
    #     # Check for word-level timestamp pattern <MM:SS.SS>
    #     word_timestamp_pattern = r"<\d+:\d+\.\d+>"

    #     # Join all lines to check for word timestamps anywhere
    #     all_text = "\n".join(lyrics_lines)
    #     if re.search(r"\[\d+:\d+\.\d+\]", all_text) and re.search(
    #         word_timestamp_pattern, all_text
    #     ):
    #         # We found both line timestamps and word timestamps somewhere
    #         word_timestamps = re.findall(word_timestamp_pattern, all_text)
    #         if len(word_timestamps) >= 2:  # At least two word timestamps
    #             return True

    #     # Original line-by-line check as backup
    #     for line in lyrics_lines[:10]:  # Check first 10 lines
    #         if re.search(r"\[\d+:\d+\.\d+\]", line) and re.search(
    #             word_timestamp_pattern, line
    #         ):
    #             word_timestamps = re.findall(word_timestamp_pattern, line)
    #             if len(word_timestamps) >= 2:
    #                 return True

    #     return False

    # def _create_enhanced_lrc_view(
    #     self, lyrics_lines: List[str], current_time: float, context_lines: int
    # ) -> str:
    #     """
    #     Create a view for enhanced LRC format with word-level highlighting.

    #     Args:
    #         lyrics_lines: Enhanced LRC lyrics lines
    #         current_time: Current playback position in seconds
    #         context_lines: Number of context lines to show

    #     Returns:
    #         Formatted lyrics with word-level highlighting
    #     """
    #     # Get the theme style for highlighting
    #     theme_style = self._get_theme_gradient_style()

    #     # Parse the enhanced LRC lines into a structured format
    #     parsed_lines = self._parse_enhanced_lrc(lyrics_lines)

    #     if not parsed_lines:
    #         return "[italic]Could not parse enhanced lyrics format[/italic]"

    #     # Find the current line based strictly on timestamps - the line we're currently in
    #     current_line_index = 0
    #     for i, line_data in enumerate(parsed_lines):
    #         line_time = line_data["timestamp"]
    #         if line_time <= current_time:
    #             current_line_index = i
    #         else:
    #             break

    #     # Calculate the range of lines to display
    #     start_index = max(0, current_line_index - context_lines)
    #     end_index = min(len(parsed_lines), current_line_index + context_lines + 1)

    #     # Build the focused lyrics display
    #     result_lines = []

    #     # Add header if not at beginning
    #     if start_index > 0:
    #         result_lines.append(f"[{theme_style['dim']}][/{theme_style['dim']}]")

    #     # Add lines with appropriate highlighting
    #     for i in range(start_index, end_index):
    #         line_data = parsed_lines[i]

    #         if i == current_line_index:
    #             # Current line - highlight words based on their timestamps
    #             line_text = self._highlight_words_by_timestamp(
    #                 line_data["words"], current_time, theme_style
    #             )
    #             result_lines.append(line_text)
    #         elif i < current_line_index:
    #             # Past lines - show as dimmed but all words visible
    #             plain_text = " ".join(word["text"] for word in line_data["words"])
    #             result_lines.append(
    #                 f"[{theme_style['dim']}]{plain_text}[/{theme_style['dim']}]"
    #             )
    #         else:
    #             # Future lines - show as very dimmed
    #             plain_text = " ".join(word["text"] for word in line_data["words"])
    #             dim_color = theme_style.get("dim", "#555555")
    #             result_lines.append(f"[{dim_color}]{plain_text}[/{dim_color}]")

    #     # Add footer if not at end
    #     if end_index < len(parsed_lines):
    #         result_lines.append(f"[{theme_style['dim']}]...[/{theme_style['dim']}]")

    #     return "\n".join(result_lines)

    # def _highlight_words_by_timestamp(
    #     self,
    #     words: List[Dict[str, Any]],
    #     current_time: float,
    #     theme_style: Dict[str, Any],
    # ) -> str:
    #     """
    #     Highlight words in a line based on their timestamps.

    #     This method only highlights words whose timestamps have passed,
    #     creating a progressive highlighting effect synchronized with playback.

    #     Args:
    #         words: List of word data dictionaries with timestamps
    #         current_time: Current playback time in seconds
    #         theme_style: Theme style dictionary

    #     Returns:
    #         Formatted string with progressive word highlighting
    #     """
    #     # Get theme colors with fallbacks
    #     theme_color = self._get_theme_color(theme_style)
    #     gradient_colors = theme_style.get("title", ["#00FF7F", "#00DD6E", "#00BB5C"])
    #     dim_color = theme_style.get("dim", "#555555")

    #     # Format each word based on its timestamp
    #     formatted_words = []

    #     # Find the current word (most recent one that should be visible)
    #     current_word_index = -1
    #     for i, word_data in enumerate(words):
    #         if word_data["timestamp"] <= current_time:
    #             current_word_index = i
    #         else:
    #             # Once we encounter a word timestamp in the future, stop
    #             break

    #     # Format each word
    #     for i, word_data in enumerate(words):
    #         word_text = word_data["text"]

    #         if i <= current_word_index:
    #             # Words that should be visible - format with gradient based on recency
    #             distance = current_word_index - i  # How far back from current word

    #             # Current word (most recent) - highlight boldly
    #             if i == current_word_index:
    #                 formatted_words.append(
    #                     f"[bold {theme_color}]{word_text}[/bold {theme_color}]"
    #                 )
    #             # Recent words - use gradient colors
    #             elif distance < len(gradient_colors):
    #                 color_index = min(distance, len(gradient_colors) - 1)
    #                 color = gradient_colors[color_index]
    #                 formatted_words.append(f"[{color}]{word_text}[/{color}]")
    #             # Words further back - use dim color
    #             else:
    #                 formatted_words.append(f"[{dim_color}]{word_text}[/{dim_color}]")
    #         else:
    #             # Words not yet reached - use very dim color
    #             formatted_words.append(f"[{dim_color}]{word_text}[/{dim_color}]")

    #     return " ".join(formatted_words)

    # def _parse_enhanced_lrc(self, lyrics_lines: List[str]) -> List[Dict[str, Any]]:
    #     """
    #     Parse enhanced LRC format into a structured format.

    #     Args:
    #         lyrics_lines: Enhanced LRC lyrics lines

    #     Returns:
    #         List of dictionaries containing line timestamps and word-level data
    #     """
    #     parsed_lines = []

    #     # If the lyrics are in a single line, try to split them properly
    #     if len(lyrics_lines) == 1 and "<" in lyrics_lines[0] and "[" in lyrics_lines[0]:
    #         # This might be cached lyrics that lost line breaks
    #         # Try to split by line timestamps
    #         split_pattern = r"(\[\d+:\d+\.\d+\])"
    #         split_parts = re.split(split_pattern, lyrics_lines[0])

    #         # Reconstruct lines properly
    #         if len(split_parts) > 2:
    #             reconstructed_lines = []
    #             i = 0
    #             while i < len(split_parts) - 1:
    #                 if re.match(r"\[\d+:\d+\.\d+\]", split_parts[i]):
    #                     reconstructed_lines.append(
    #                         f"{split_parts[i]}{split_parts[i + 1]}"
    #                     )
    #                     i += 2
    #                 else:
    #                     i += 1

    #             if reconstructed_lines:
    #                 logger.debug("Reconstructed enhanced LRC lines from cached format")
    #                 lyrics_lines = reconstructed_lines

    #     # Continue with the normal parsing
    #     for line in lyrics_lines:
    #         # Skip empty lines
    #         if not line.strip():
    #             continue

    #         # Extract line timestamp
    #         line_match = re.search(r"\[(\d+):(\d+\.\d+)\]", line)
    #         if not line_match:
    #             continue

    #         minutes = int(line_match.group(1))
    #         seconds = float(line_match.group(2))
    #         line_timestamp = minutes * 60 + seconds

    #         # Extract word timestamps and text
    #         words_data = []
    #         word_pattern = r"<(\d+):(\d+\.\d+)>\s*([^<]+)"

    #         # Remove the line timestamp for word processing
    #         line_without_timestamp = re.sub(r"\[\d+:\d+\.\d+\]", "", line).strip()

    #         word_matches = re.finditer(word_pattern, line_without_timestamp)
    #         for match in word_matches:
    #             word_minutes = int(match.group(1))
    #             word_seconds = float(match.group(2))
    #             word_timestamp = word_minutes * 60 + word_seconds
    #             word_text = match.group(3).strip()

    #             if word_text:
    #                 words_data.append({"timestamp": word_timestamp, "text": word_text})

    #         # Only add lines that have word data
    #         if words_data:
    #             parsed_lines.append({"timestamp": line_timestamp, "words": words_data})

    #     # Sort by timestamp
    #     if parsed_lines:
    #         parsed_lines.sort(key=lambda x: x["timestamp"])
    #         return parsed_lines

    #     # If standard parsing failed, try an alternative approach for cached lyrics
    #     if any("<" in line for line in lyrics_lines):
    #         logger.debug("Trying alternative parsing for enhanced LRC")
    #         return self._parse_enhanced_lrc_alternative(lyrics_lines)

    #     return []

    # def _parse_enhanced_lrc_alternative(
    #     self, lyrics_lines: List[str]
    # ) -> List[Dict[str, Any]]:
    #     """
    #     Alternative parsing approach for enhanced LRC that might be in non-standard format.

    #     Args:
    #         lyrics_lines: Enhanced LRC lyrics lines

    #     Returns:
    #         List of dictionaries containing line timestamps and word-level data
    #     """
    #     parsed_lines = []

    #     # Join all lyrics to handle potential formatting issues
    #     all_lyrics = " ".join(lyrics_lines)

    #     # Extract all line timestamps and their content
    #     line_pattern = r"\[(\d+):(\d+\.\d+)\](.*?)(?=\[\d+:\d+\.\d+\]|$)"
    #     line_matches = re.finditer(line_pattern, all_lyrics)

    #     for line_match in line_matches:
    #         line_minutes = int(line_match.group(1))
    #         line_seconds = float(line_match.group(2))
    #         line_timestamp = line_minutes * 60 + line_seconds
    #         line_content = line_match.group(3).strip()

    #         if not line_content:
    #             continue

    #         # Extract word timestamps and text
    #         words_data = []
    #         word_pattern = r"<(\d+):(\d+\.\d+)>\s*([^<]+)"
    #         word_matches = re.finditer(word_pattern, line_content)

    #         for match in word_matches:
    #             word_minutes = int(match.group(1))
    #             word_seconds = float(match.group(2))
    #             word_timestamp = word_minutes * 60 + word_seconds
    #             word_text = match.group(3).strip()

    #             if word_text:
    #                 words_data.append({"timestamp": word_timestamp, "text": word_text})

    #         # Only add lines that have word data
    #         if words_data:
    #             parsed_lines.append({"timestamp": line_timestamp, "words": words_data})

    #     # Sort by timestamp
    #     if parsed_lines:
    #         parsed_lines.sort(key=lambda x: x["timestamp"])

    #     return parsed_lines

    def _highlight_current_word(
        self,
        words: List[Dict[str, Any]],
        current_word_index: int,
        theme_style: Dict[str, Any],
    ) -> str:
        """
        Create a string with the current word highlighted using a gradient effect.

        Args:
            words: List of word data dictionaries
            current_word_index: Index of the current word
            theme_style: Theme style dictionary

        Returns:
            Formatted string with prominent gradient word highlighting
        """
        # Get theme colors with fallbacks
        theme_color = self._get_theme_color(theme_style)
        gradient_colors = theme_style.get("title", ["#00FF7F", "#00DD6E", "#00BB5C"])
        dim_color = theme_style.get("dim", "#555555")

        # Format each word based on its distance from the current word
        formatted_words = []
        for i, word_data in enumerate(words):
            word_text = word_data["text"]
            distance = abs(i - current_word_index)

            formatted_words.append(
                self._format_word_with_gradient(
                    word_text, distance, theme_color, gradient_colors, dim_color
                )
            )

        return " ".join(formatted_words)

    def _format_word_with_gradient(
        self,
        word: str,
        distance: int,
        theme_color: str,
        gradient_colors: List[str],
        dim_color: str,
    ) -> str:
        """Format a single word based on its distance from the current word."""
        # Current or adjacent word - use primary color and bold
        if distance <= 1:
            return f"[bold {theme_color}]{word}[/bold {theme_color}]"

        # Words within gradient range - use gradient colors
        if distance <= len(gradient_colors) + 1:
            # Index into gradient colors, with bounds checking
            color_index = min(distance - 2, len(gradient_colors) - 1)
            color_index = max(0, color_index)  # Ensure non-negative
            color = gradient_colors[color_index]
            return f"[{color}]{word}[/{color}]"

        # Far words - use dim color
        return f"[{dim_color}]{word}[/{dim_color}]"

    # Helper method to get theme color with fallbacks
    def _get_theme_color(self, theme_style: Dict[str, Any]) -> str:
        """Get the primary theme color with appropriate fallbacks."""
        return theme_style.get("primary", theme_style.get("title", ["#00FF7F"])[0])

    def _get_plain_lyrics(self, lyrics_lines: List[str]) -> List[str]:
        """
        Extract plain text from any type of lyrics format.

        Args:
            lyrics_lines: List of lyrics lines (can be synced, enhanced LRC, or plain)

        Returns:
            List of plain lyrics lines without timestamps
        """
        plain_lines = []

        # Handle enhanced LRC format
        if self._is_enhanced_lrc(lyrics_lines):
            for line in lyrics_lines:
                # Remove line timestamp
                line_without_time = re.sub(r"\[\d+:\d+\.\d+\]", "", line).strip()
                # Remove word timestamps
                plain_line = re.sub(r"<\d+:\d+\.\d+>", "", line_without_time).strip()
                if plain_line:
                    plain_lines.append(plain_line)

        # Handle standard LRC format
        elif self._is_synced_lyrics(lyrics_lines):
            for line in lyrics_lines:
                # Remove timestamp patterns
                plain_line = re.sub(r"\[\d+:\d+\.\d+\]", "", line).strip()
                if plain_line:
                    plain_lines.append(plain_line)

        # Already plain lyrics
        else:
            plain_lines = [line.strip() for line in lyrics_lines if line.strip()]

        return plain_lines
