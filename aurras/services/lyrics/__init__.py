"""
Lyrics Module Package

This package provides functionality for fetching synced and plain lyrics for songs.
"""

from .manager import LyricsManager
from .cache import LyricsCache
from .fetcher import LyricsFetcher
from .parser import LyricsParser
from .formatter import LyricsFormatter

__all__ = [
    "LyricsManager",
    "LYRICS_AVAILABLE",
    "LyricsCache",
    "LyricsFetcher",
    "LyricsParser",
    "LyricsFormatter",
]
