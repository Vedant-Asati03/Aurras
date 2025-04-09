"""
Lyrics Module Package

This package provides functionality for fetching synced and plain lyrics for songs.
"""

# Check if syncedlyrics is available
try:
    import syncedlyrics

    LYRICS_AVAILABLE = True
except ImportError:
    LYRICS_AVAILABLE = False

# Import after defining LYRICS_AVAILABLE to avoid circular imports
from .manager import LyricsManager
from .cache import LyricsCache
from .fetcher import LyricsFetcher

__all__ = ["LyricsManager", "LyricsCache", "LyricsFetcher", "LYRICS_AVAILABLE"]
