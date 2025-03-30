"""Lyrics handler for the MPV player."""

import logging
import re
from typing import Dict, List, Optional, Tuple, Any, Union

try:
    from ..services.lyrics import LyricsManager, LYRICS_AVAILABLE
except ImportError:
    LYRICS_AVAILABLE = False
    LyricsManager = None

from ..utils.exceptions import LyricsError

# Set up logging
logger = logging.getLogger(__name__)


class LyricsHandler:
    """
    A dedicated handler for fetching, caching, and processing lyrics.

    This class separates lyrics-handling logic from the player implementation,
    providing a cleaner separation of concerns.

    Attributes:
        lyrics_manager: The LyricsManager instance for retrieving lyrics
        lyrics_cache: A cache for storing retrieved lyrics
    """

    def __init__(self) -> None:
        """Initialize the lyrics handler."""
        self.lyrics_manager = (
            LyricsManager() if LYRICS_AVAILABLE and LyricsManager else None
        )
        self.lyrics_cache: Dict[str, List[str]] = {}
        self.parsed_synced_lyrics: Dict[
            str, List[Tuple[float, str]]
        ] = {}  # Cache for parsed synchronized lyrics
        self.lyrics_available = LYRICS_AVAILABLE and self.lyrics_manager is not None

    @staticmethod
    def _normalize_str(s: Optional[str]) -> str:
        """
        Normalize a string for more reliable cache lookups.

        Args:
            s: The string to normalize

        Returns:
            Normalized string (lowercase, trimmed, or empty string if None/Unknown)
        """
        if not s or s == "Unknown":
            return ""
        return s.lower().strip()

    def _generate_cache_keys(
        self, song: str, artist: str, album: str
    ) -> Tuple[str, str]:
        """
        Generate cache keys for lyrics lookup.

        Args:
            song: Song name
            artist: Artist name
            album: Album name

        Returns:
            Tuple of (full_key, song_only_key)
        """
        # Create a full key with all metadata
        full_key = f"{self._normalize_str(song)}_{self._normalize_str(artist)}_{self._normalize_str(album)}"

        # Create a fallback key with just the song name
        song_only_key = self._normalize_str(song)

        return full_key, song_only_key

    def get_from_cache(self, song: str, artist: str, album: str) -> Optional[List[str]]:
        """
        Retrieve lyrics from cache if available.

        Args:
            song: Song name
            artist: Artist name
            album: Album name

        Returns:
            Cached lyrics if found, None otherwise
        """
        full_key, song_only_key = self._generate_cache_keys(song, artist, album)

        # Try full key first (most specific match)
        if full_key in self.lyrics_cache:
            logger.debug(f"Using memory-cached lyrics for '{song}' (full key match)")
            return self.lyrics_cache[full_key]

        # Fall back to song-only key
        if song_only_key in self.lyrics_cache:
            logger.debug(
                f"Using memory-cached lyrics for '{song}' (song-only key match)"
            )
            return self.lyrics_cache[song_only_key]

        # Not found in cache
        return None

    def store_in_cache(
        self, lyrics: List[str], song: str, artist: str, album: str
    ) -> None:
        """
        Store lyrics in cache with appropriate keys.

        Args:
            lyrics: The lyrics to cache
            song: Song name
            artist: Artist name
            album: Album name
        """
        full_key, song_only_key = self._generate_cache_keys(song, artist, album)

        # Store with both keys for better future matching
        self.lyrics_cache[full_key] = lyrics
        self.lyrics_cache[song_only_key] = lyrics

        logger.debug(f"Cached lyrics for '{song}' with {len(lyrics)} lines")

        # Clear any previously parsed synchronized lyrics for this song
        if full_key in self.parsed_synced_lyrics:
            del self.parsed_synced_lyrics[full_key]
        if song_only_key in self.parsed_synced_lyrics:
            del self.parsed_synced_lyrics[song_only_key]

    def fetch_lyrics(
        self, song_name: str, artist_name: str, album_name: str, duration: float
    ) -> List[str]:
        """
        Fetch lyrics for a song, handling various error cases gracefully.

        Args:
            song_name: Name of the song
            artist_name: Artist name
            album_name: Album name
            duration: Song duration in seconds

        Returns:
            List of lyrics lines or appropriate error message
        """
        # Return early if lyrics manager is not available
        if not self.lyrics_available:
            return ["[italic yellow]Lyrics feature not available[/italic yellow]"]

        # Check if we have valid inputs
        if not song_name or song_name == "Unknown":
            return ["[italic yellow]Waiting for song information...[/italic yellow]"]

        # Validate metadata is not default values
        valid_metadata = True
        if artist_name == "Unknown" or not artist_name.strip():
            logger.debug("Artist name not available for lyrics fetch")
            valid_metadata = False

        if album_name == "Unknown" or not album_name.strip():
            logger.debug("Album name not available for lyrics fetch")
            valid_metadata = False

        if duration <= 0:
            logger.debug("Duration not available for lyrics fetch")
            valid_metadata = False

        if not valid_metadata:
            return [
                "[italic yellow]Waiting for complete song metadata...[/italic yellow]"
            ]

        # We should use integers for duration when obtaining lyrics
        duration_int = int(duration) if duration else 0

        logger.debug(
            f"Fetching lyrics for: '{song_name}' by '{artist_name}' from album '{album_name}' (duration: {duration_int}s)"
        )

        try:
            # The LyricsManager.obtain_lyrics_info method will check the database cache first
            lyrics_info = self.lyrics_manager.obtain_lyrics_info(
                song_name, artist_name, album_name, duration_int
            )

            if not lyrics_info:
                logger.info(f"No lyrics info returned for: {song_name}")
                return [
                    f"[italic yellow]No lyrics found for:[/italic yellow] [bold]{song_name}[/bold]"
                ]

            # Add detailed logging of what we received
            logger.debug(f"Lyrics info keys received: {', '.join(lyrics_info.keys())}")

            # Try to get synchronized lyrics first
            if "synced_lyrics" in lyrics_info and lyrics_info["synced_lyrics"]:
                return self._process_synced_lyrics(
                    lyrics_info["synced_lyrics"], song_name
                )

            # Fall back to plain lyrics if no synchronized lyrics
            if "plain_lyrics" in lyrics_info and lyrics_info["plain_lyrics"]:
                return self._process_plain_lyrics(
                    lyrics_info["plain_lyrics"], song_name
                )

            # No lyrics found
            logger.info(f"No lyrics found for: {song_name}")
            return [
                f"[italic yellow]No lyrics found for:[/italic yellow] [bold]{song_name}[/bold]"
            ]

        except Exception as e:
            logger.error(f"Error fetching lyrics: {e}")
            raise LyricsError(f"Error fetching lyrics: {e}")

    def _process_synced_lyrics(
        self, synced_lyrics: Union[str, List[str]], song_name: str
    ) -> List[str]:
        """
        Process synchronized lyrics, handling different input formats.

        Args:
            synced_lyrics: Synchronized lyrics as string or list
            song_name: Name of the song (for error messages)

        Returns:
            List of lyrics lines
        """
        # Convert to list if we got a string
        if isinstance(synced_lyrics, str):
            # Split string into lines
            lyrics_list = synced_lyrics.split("\n")
            logger.debug(
                f"Converted synced lyrics string to list of {len(lyrics_list)} lines"
            )
        elif isinstance(synced_lyrics, list):
            # Already a list
            lyrics_list = synced_lyrics
            logger.debug(
                f"Received synced lyrics as list with {len(lyrics_list)} lines"
            )
        else:
            # Convert anything else to string and split
            lyrics_list = str(synced_lyrics).split("\n")
            logger.debug(
                f"Converted synced lyrics of type {type(synced_lyrics)} to list"
            )

        # Make sure we have at least one line
        if not lyrics_list:
            lyrics_list = [
                f"[italic yellow]Empty lyrics for:[/italic yellow] [bold]{song_name}[/bold]"
            ]
            logger.debug("Lyrics list was empty, using placeholder")

        logger.info(
            f"Found synchronized lyrics for: {song_name} ({len(lyrics_list)} lines)"
        )
        return lyrics_list

    def _process_plain_lyrics(
        self, plain_lyrics: Union[str, List[str]], song_name: str
    ) -> List[str]:
        """
        Process plain (non-synchronized) lyrics.

        Args:
            plain_lyrics: Plain lyrics as string or list
            song_name: Name of the song (for logging)

        Returns:
            List of lyrics lines
        """
        if isinstance(plain_lyrics, str):
            lyrics_list = plain_lyrics.split("\n")
        else:
            lyrics_list = str(plain_lyrics).split("\n")

        logger.info(f"Found non-synced lyrics for: {song_name}")
        return lyrics_list

    def parse_synced_lyrics(self, lyrics_lines: List[str]) -> List[Tuple[float, str]]:
        """
        Parse synchronized lyrics timestamps and text into a structured format.

        Args:
            lyrics_lines: List of lyrics lines with timestamps

        Returns:
            List of (timestamp, text) tuples sorted by timestamp
        """
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

        return parsed_lyrics

    def get_or_parse_synced_lyrics(
        self, lyrics_lines: List[str], song: str, artist: str, album: str
    ) -> List[Tuple[float, str]]:
        """
        Get parsed synchronized lyrics from cache or parse them if not available.

        Args:
            lyrics_lines: List of lyrics lines with timestamps
            song: Song name
            artist: Artist name
            album: Album name

        Returns:
            List of (timestamp, text) tuples sorted by timestamp
        """
        full_key, song_only_key = self._generate_cache_keys(song, artist, album)

        # Check if we've already parsed these lyrics
        if full_key in self.parsed_synced_lyrics:
            return self.parsed_synced_lyrics[full_key]

        # Parse the lyrics and cache the result
        parsed = self.parse_synced_lyrics(lyrics_lines)
        self.parsed_synced_lyrics[full_key] = parsed
        self.parsed_synced_lyrics[song_only_key] = parsed  # Also cache with simpler key

        return parsed

    def create_focused_lyrics_view(
        self,
        lyrics_lines: List[str],
        current_time: float,
        song: str,
        artist: str,
        album: str,
        context_lines: int = 3,
    ) -> str:
        """
        Create a focused view of lyrics with the current line highlighted.

        Args:
            lyrics_lines: List of lyrics lines with timestamps
            current_time: Current playback position in seconds
            song: Song name for caching parsed lyrics
            artist: Artist name for caching parsed lyrics
            album: Album name for caching parsed lyrics
            context_lines: Number of lines to show above and below current line

        Returns:
            Formatted lyrics text with highlighting
        """
        if not lyrics_lines:
            return "[italic]No lyrics available[/italic]"

        # Check if these are synced lyrics (contain timestamps)
        has_timestamps = any(
            re.search(r"\[\d+:\d+\.\d+\]", line) for line in lyrics_lines[:5]
        )

        if not has_timestamps:
            # For regular lyrics, just join them with limited lines
            result = "\n".join(lyrics_lines[:6])
            if len(lyrics_lines) > 6:
                result += "\n[dim]...[/dim]"
            return result

        # Get parsed synchronized lyrics (from cache if available)
        parsed_lyrics = self.get_or_parse_synced_lyrics(
            lyrics_lines, song, artist, album
        )

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

        # Add a header if we're not at the beginning
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

    def has_lyrics_support(self) -> bool:
        """Check if lyrics support is available."""
        return self.lyrics_available
