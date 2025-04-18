"""
Lyrics fetching module.

This module provides functionality for fetching lyrics from APIs and services.
"""

import threading
import requests
from typing import Dict
from rich.console import Console

from .cache import LyricsCache

# Check if syncedlyrics is available rather than importing from __init__
try:
    import syncedlyrics

    LYRICS_AVAILABLE = True
except ImportError:
    LYRICS_AVAILABLE = False

console = Console()


class LyricsFetcher:
    """Fetcher class to handle fetching lyrics from the API."""

    def __init__(
        self, track_name: str, artist_name: str, album_name: str, duration: int
    ):
        """
        Initialize the LyricsFetcher.

        Args:
            track_name: Name of the track
            artist_name: Name of the artist
            album_name: Name of the album
            duration: Duration of the track in seconds
        """
        self.lyrics = None
        self.lock = threading.Lock()
        self.track_name = track_name
        self.artist_name = artist_name
        self.album_name = album_name
        self.duration = duration
        self.cache = LyricsCache()

    def fetch_lyrics(self) -> Dict[str, list]:
        """
        Fetch lyrics, first checking cache then the API.

        Returns:
            Dictionary with 'synced_lyrics' and 'plain_lyrics' keys
        """
        # First check the cache
        cached_lyrics = self.cache.load_lyrics_from_db(
            self.track_name, self.artist_name, self.album_name, self.duration
        )

        if cached_lyrics:
            return cached_lyrics

        if not LYRICS_AVAILABLE:
            return {"synced_lyrics": "", "plain_lyrics": ""}

        with self.lock:
            try:
                self.lyrics = syncedlyrics.search(
                    f"{self.track_name} - {self.artist_name}"
                )

                synced_lyrics = (
                    syncedlyrics.search(
                        f"{self.track_name} - {self.artist_name}",
                        synced_only=True,
                    )
                    or ""
                )
                plain_lyrics = (
                    syncedlyrics.search(
                        f"{self.track_name} - {self.artist_name}",
                        plain_only=True,
                    )
                    or ""
                )

                synced_lyrics_list = synced_lyrics.split("\n") if synced_lyrics else []
                plain_lyrics_list = plain_lyrics.split("\n") if plain_lyrics else []

                # Save to cache
                self.cache.save_lyrics(
                    self.track_name,
                    self.artist_name,
                    self.album_name,
                    self.duration,
                    synced_lyrics_list,
                    plain_lyrics_list,
                )

                return {
                    "synced_lyrics": synced_lyrics_list,
                    "plain_lyrics": plain_lyrics_list,
                }
            except requests.RequestException as e:
                console.print(f"[red]Error fetching lyrics: {e}[/red]")
                return {"synced_lyrics": "", "plain_lyrics": ""}
            except Exception as e:
                console.print(f"[red]Error in lyrics fetcher: {e}[/red]")
                return {"synced_lyrics": "", "plain_lyrics": ""}
