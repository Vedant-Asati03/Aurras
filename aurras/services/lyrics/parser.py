"""
Lyrics parser module.

This module provides functionality for parsing and processing lyrics formats.
"""

import re
from typing import List, Tuple

TIMESTAMP_PATTERN = r"\[(\d+):(\d+\.\d+)\]"
WORD_TIMESTAMP_PATTERN = r"<\d+:\d+\.\d+>"
LINE_TIMESTAMP_PATTERN = r"\[\d+:\d+\.\d+\]"
WORD_PATTERN = r"<(\d+):(\d+\.\d+)>\s*([^<]+)"
LINE_PATTERN = r"\[(\d+):(\d+\.\d+)\](.*?)(?=\[\d+:\d+\.\d+\]|$)"


class LyricsParser:
    """Parser for different lyrics formats with support for synced and plain lyrics."""

    @staticmethod
    def is_synced_lyrics(lyrics_lines: List[str]) -> bool:
        """
        Check if lyrics are synced (contain timestamps).

        Args:
            lyrics_lines: Lyrics lines to check

        Returns:
            True if lyrics appear to be synced
        """
        # Check a few lines for timestamp patterns
        timestamp_pattern = r"\[\d+:\d+\.\d+\]"
        for line in lyrics_lines[:10]:  # Check first 10 lines
            if re.search(timestamp_pattern, line):
                return True
        return False

    @staticmethod
    def _extract_plain_lyrics(lyrics_lines: List[str]) -> List[str]:
        """
        Extract plain text from synced lyrics.

        Args:
            lyrics_lines: Synced lyrics lines

        Returns:
            Plain lyrics without timestamps
        """
        plain_lines = []
        for line in lyrics_lines:
            # Remove timestamp patterns
            plain_line = re.sub(r"\[\d+:\d+\.\d+\]", "", line).strip()
            if plain_line:
                plain_lines.append(plain_line)
        return plain_lines

    @staticmethod
    def get_plain_lyrics(lyrics_lines: List[str]) -> List[str]:
        """
        Extract plain text from any type of lyrics format.

        Args:
            lyrics_lines: List of lyrics lines (can be synced, enhanced LRC, or plain)

        Returns:
            List of plain lyrics lines without timestamps
        """
        # Check if these are synced lyrics
        if LyricsParser.is_synced_lyrics(lyrics_lines):
            return LyricsParser._extract_plain_lyrics(lyrics_lines)

        # Already plain lyrics
        return [line.strip() for line in lyrics_lines if line.strip()]

    @staticmethod
    def parse_synced_lyrics(lyrics_lines: List[str]) -> List[Tuple[float, str]]:
        """
        Parse synced lyrics into a list of (timestamp, text) tuples.

        Args:
            lyrics_lines: List of lyrics lines with timestamps

        Returns:
            List of (timestamp, text) tuples
        """
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

    @staticmethod
    def find_current_lyric_index(
        parsed_lyrics: List[Tuple[float, str]], current_time: float
    ) -> int:
        """
        Find the index of the current lyric based on playback time.

        Args:
            parsed_lyrics: List of (timestamp, text) tuples
            current_time: Current playback position in seconds

        Returns:
            Index of the current lyric
        """
        for i, (timestamp, _) in enumerate(parsed_lyrics):
            if timestamp > current_time:
                return max(0, i - 1)
        # If we get here, we're at the last line
        return len(parsed_lyrics) - 1
