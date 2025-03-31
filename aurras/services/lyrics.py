"""
Lyrics Module

This module provides functionality for fetching synced and plain lyrics for a song.
"""

import threading
import sqlite3
import re
import time
import os
import json
import requests
from typing import List, Tuple, Optional, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.box import ROUNDED
from rich.text import Text
from ..utils.path_manager import PathManager

_path_manager = PathManager()
console = Console()


try:
    from lrclib import LrcLibAPI

    LYRICS_AVAILABLE = True
except ImportError:
    LYRICS_AVAILABLE = False
    console.print(
        "[red]Warning: lrclib not installed. Lyrics will not be available.[/red]"
    )
    console.print(
        "[yellow]To enable lyrics, install with: pip install lrclibapi[/yellow]"
    )


class SetupAPI:
    """
    SetupAPI class to manage the API instance.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SetupAPI, cls).__new__(cls)
            cls._instance.api = LrcLibAPI(user_agent="aurras/0.0.1")
        return cls._instance


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


class LyricsFetcher:
    """Fetcher class to handle fetching lyrics from the API."""

    def __init__(
        self, track_name: str, artist_name: str, album_name: str, duration: int
    ):
        self.api = SetupAPI().api
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

        # If not in cache, fetch from API
        with self.lock:
            try:
                self.lyrics = self.api.get_lyrics(
                    track_name=self.track_name,
                    artist_name=self.artist_name,
                    album_name=self.album_name,
                    duration=self.duration,
                )

                synced_lyrics = self.lyrics.synced_lyrics.split("\n") or []
                plain_lyrics = self.lyrics.plain_lyrics.split("\n") or []

                # Save to cache
                self.cache.save_lyrics(
                    self.track_name,
                    self.artist_name,
                    self.album_name,
                    self.duration,
                    synced_lyrics,
                    plain_lyrics,
                )

                return {"synced_lyrics": synced_lyrics, "plain_lyrics": plain_lyrics}
            except requests.RequestException as e:
                console.print(f"[red]Error fetching lyrics: {e}[/red]")
                return {"synced_lyrics": "", "plain_lyrics": ""}


class LyricsManager:
    """
    LyricsManager class to handle fetching and displaying lyrics.
    """

    def __init__(
        self,
        settings: Optional[Dict[str, str]] = None,
    ):
        self.console = Console()
        self.settings = settings or self._load_default_settings()
        self.lyrics_fetcher = None
        self.lyrics_data = {"synced_lyrics": "", "plain_lyrics": ""}

    def _load_default_settings(self) -> Dict[str, str]:
        """Load default settings or from config file if available."""
        default_settings = {"show-lyrics": "yes"}

        config_path = str(_path_manager.config_file)
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    loaded_settings = json.load(f)
                    default_settings.update(loaded_settings)
            except (json.JSONDecodeError, IOError):
                pass

        return default_settings

    def obtain_lyrics_info(
        self,
        track_name: str,
        artist_name: str,
        album_name: str,
        duration: int,
    ) -> Dict[str, list]:
        """Fetch lyrics using LyricsFetcher."""
        if not self._should_show_lyrics():
            # return {"synced_lyrics": "", "plain_lyrics": ""}
            return None

        if not LYRICS_AVAILABLE:
            # return {"synced_lyrics": "", "plain_lyrics": ""}
            return None

        try:
            self.lyrics_fetcher = LyricsFetcher(
                track_name, artist_name, album_name, duration
            )
            return self.lyrics_fetcher.fetch_lyrics()
        except Exception as e:
            console.print(f"[red]Error in lyrics manager: {e}[/red]")
            return {"synced_lyrics": "", "plain_lyrics": ""}

    def _should_show_lyrics(self) -> bool:
        """Check if lyrics should be shown based on settings and available modules."""
        if not LYRICS_AVAILABLE:
            return False

        return self.settings.get("show-lyrics", "yes").lower() == "yes"

    def display_lyrics(self, current_time: float) -> None:
        """
        Display the lyrics for the current time in the song.

        Args:
            current_time: Current playback time in seconds
        """
        if not self._should_show_lyrics() or not self.lyrics_data["synced_lyrics"]:
            return

        synced_lyrics = self.lyrics_data["synced_lyrics"].split("\n")

        # Find the current line based on timestamps (basic LRC format parsing)
        current_line = ""
        next_line = ""
        for i, line in enumerate(synced_lyrics):
            timestamp_match = re.match(r"\[(\d+):(\d+\.\d+)\](.*)", line)
            if timestamp_match:
                mins, secs, text = timestamp_match.groups()
                line_time = int(mins) * 60 + float(secs)

                if line_time <= current_time:
                    current_line = text.strip()

                    # Look for next line
                    if i < len(synced_lyrics) - 1:
                        next_match = re.match(
                            r"\[(\d+):(\d+\.\d+)\](.*)", synced_lyrics[i + 1]
                        )
                        if next_match:
                            next_line = next_match.group(3).strip()
                    break

        # Display the current lyrics
        if current_line:
            styled_text = Text()
            styled_text.append(current_line, style="bold green")
            if next_line:
                styled_text.append("\n" + next_line, style="dim white")

            self.console.print(
                Panel(
                    styled_text,
                    title="[bold]Lyrics[/bold]",
                    box=ROUNDED,
                    border_style="green",
                )
            )
