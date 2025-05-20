"""
Lyrics manager module.

This module provides the main manager class for handling lyrics operations.
It serves as the primary interface between the lyrics service and the rest of the application.
"""

from typing import List

from aurras.core.settings import SETTINGS
from aurras.utils.logger import get_logger
from aurras.services.lyrics.cache import LyricsCache
from aurras.services.lyrics.parser import LyricsParser
from aurras.services.lyrics.fetcher import LyricsFetcher
from aurras.services.lyrics.formatter import LyricsFormatter

logger = get_logger("aurras.services.lyrics.manager", log_to_console=False)


class LyricsManager:
    """
    LyricsManager class to coordinate all lyrics-related operations.

    This class serves as the main interface for lyrics functionality, coordinating
    between cache, fetcher, parser, and formatter components.
    """

    def __init__(self):
        """
        Initialize the LyricsManager with all necessary components.
        """
        self.lyrics_cache = LyricsCache()
        self.lyrics_parser = LyricsParser()
        self.lyrics_formatter = LyricsFormatter()

    @property
    def settings(self):
        """Get the current settings."""
        return SETTINGS.appearance_settings

    def has_lyrics_support(self) -> bool:
        """
        Check if lyrics support is available based on settings.

        Returns:
            True if lyrics support is available, False otherwise
        """
        try:
            return self._should_show_lyrics()
        except Exception as e:
            logger.error(f"Error checking lyrics support: {e}")
            return False

    def _should_show_lyrics(self) -> bool:
        """
        Check if lyrics should be shown based on settings.

        Returns:
            True if lyrics should be shown, False otherwise
        """
        return self.settings.display_lyrics.lower() == "yes"

    # --- Public API Methods ---

    def fetch_lyrics(
        self, song: str, artist: str, album: str, duration: int
    ) -> List[str]:
        """
        Fetch lyrics for a song, checking cache first before using the lyrics service.

        Args:
            song: Song name
            artist: Artist name
            album: Album name
            duration: Song duration in seconds

        Returns:
            List of lyrics lines
        """
        try:
            # Skip if lyrics are disabled or song title is missing
            if not self._should_show_lyrics():
                logger.debug("Lyrics display is disabled in settings")
                return []

            if not song or song == "Unknown" or not song.strip():
                logger.warning("Cannot fetch lyrics: missing song title")
                return []

            # Try to get from cache first
            cached_lyrics = self.lyrics_cache.get_from_cache(song, artist, album)
            if cached_lyrics:
                return cached_lyrics

            # Log what we're searching for
            logger.info(
                f"Fetching lyrics for: Song='{song}', Artist='{artist}', Album='{album}'"
            )

            # Create a fetcher for this request
            lyrics_fetcher = LyricsFetcher(song, artist, album, duration)
            lyrics_data = lyrics_fetcher.fetch_lyrics()

            if not lyrics_data:
                logger.info(f"No lyrics found for '{song}'")
                return []

            # Extract synced lyrics if available, otherwise use plain lyrics
            lyrics_lines = []

            if synced_lyrics := lyrics_data.get("synced_lyrics"):
                lyrics_lines = (
                    synced_lyrics
                    if isinstance(synced_lyrics, list)
                    else synced_lyrics.splitlines()
                )
                if lyrics_lines:
                    # Store in cache for future use
                    self.lyrics_cache.store_in_cache(
                        lyrics_lines, song, artist, album, duration
                    )
                    logger.info(f"Found synced lyrics for '{song}'")
                    return lyrics_lines

            # Fall back to plain lyrics
            if plain_lyrics := lyrics_data.get("plain_lyrics"):
                lyrics_lines = (
                    plain_lyrics
                    if isinstance(plain_lyrics, list)
                    else plain_lyrics.splitlines()
                )
                if lyrics_lines:
                    # Store in cache for future use
                    self.lyrics_cache.store_in_cache(
                        lyrics_lines, song, artist, album, duration
                    )
                    logger.info(f"Found plain lyrics for '{song}'")
                    return lyrics_lines

            # No usable lyrics found
            logger.info(f"No usable lyrics found for '{song}'")
            return []

        except Exception as e:
            logger.error(f"Error fetching lyrics: {e}")
            from aurras.utils.exceptions import LyricsError

            raise LyricsError(f"Failed to fetch lyrics: {e}")

    def store_in_cache(
        self, lyrics: List[str], song: str, artist: str, album: str
    ) -> None:
        """
        Store lyrics in cache.

        Args:
            lyrics: List of lyrics lines
            song: Song name
            artist: Artist name
            album: Album name
        """
        self.lyrics_cache.store_in_cache(lyrics, song, artist, album)

    def get_no_lyrics_message(self) -> str:
        """
        Get a themed "no lyrics available" message.

        Returns:
            A formatted message indicating no lyrics are available
        """
        return self.lyrics_formatter.get_no_lyrics_message()

    def get_waiting_message(self) -> str:
        """
        Get a themed "waiting for lyrics" message.

        Returns:
            A formatted message indicating lyrics are being fetched
        """
        return self.lyrics_formatter.get_waiting_message()

    def get_error_message(self, error_text: str) -> str:
        """
        Get a themed error message.

        Args:
            error_text: The error text to display

        Returns:
            A formatted error message
        """
        return self.lyrics_formatter.get_error_message(error_text)

    def create_focused_lyrics_view(
        self,
        lyrics_lines: List[str],
        current_time: float,
        duration: float,
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
        return self.lyrics_formatter.create_focused_lyrics_view(
            lyrics_lines, current_time, duration, context_lines, plain_mode
        )

    # --- Additional access to internal components ---

    def _is_synced_lyrics(self, lyrics_lines: List[str]) -> bool:
        """
        Check if lyrics are synced (contain timestamps).

        Args:
            lyrics_lines: Lyrics lines to check

        Returns:
            True if lyrics appear to be synced
        """
        return LyricsParser.is_synced_lyrics(lyrics_lines)

    def _get_plain_lyrics(self, lyrics_lines: List[str]) -> List[str]:
        """
        Extract plain text from any type of lyrics format.

        Args:
            lyrics_lines: List of lyrics lines (can be synced, enhanced LRC, or plain)

        Returns:
            List of plain lyrics lines without timestamps
        """
        return LyricsParser.get_plain_lyrics(lyrics_lines)
