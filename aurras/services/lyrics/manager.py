"""
Lyrics manager module.

This module provides the main manager class for handling lyrics operations.
"""

import os
import re
import json
from typing import Optional, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.box import ROUNDED
from rich.text import Text

from ...utils.path_manager import PathManager
from .fetcher import LyricsFetcher

# Check if syncedlyrics is available rather than importing from __init__
try:
    import syncedlyrics

    LYRICS_AVAILABLE = True
except ImportError:
    LYRICS_AVAILABLE = False

_path_manager = PathManager()
console = Console()


class LyricsManager:
    """
    LyricsManager class to handle fetching and displaying lyrics.
    """

    def __init__(
        self,
        settings: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize the LyricsManager.

        Args:
            settings: Optional settings dictionary
        """
        self.console = Console()
        self.settings = settings or self._load_default_settings()
        self.lyrics_fetcher = None
        self.lyrics_data = {"synced_lyrics": "", "plain_lyrics": ""}

    def _load_default_settings(self) -> Dict[str, str]:
        """
        Load default settings or from config file if available.

        Returns:
            Dictionary of settings
        """
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
        """
        Fetch lyrics using LyricsFetcher.

        Args:
            track_name: Name of the track
            artist_name: Name of the artist
            album_name: Name of the album
            duration: Duration of the track in seconds

        Returns:
            Dictionary with 'synced_lyrics' and 'plain_lyrics' keys
        """
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
        """
        Check if lyrics should be shown based on settings and available modules.

        Returns:
            True if lyrics should be shown, False otherwise
        """
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

    def format_lyrics(self, lyrics_data: Dict[str, Any]) -> str:
        """
        Format lyrics for display.

        Args:
            lyrics_data: Dictionary with lyrics data

        Returns:
            Formatted lyrics text
        """
        if not lyrics_data:
            return "No lyrics available."

        # Prefer synced lyrics if available
        lyrics = lyrics_data.get("synced_lyrics", "")

        if not lyrics:
            # Fall back to plain lyrics
            lyrics = lyrics_data.get("plain_lyrics", "")

        if isinstance(lyrics, list):
            return "\n".join(lyrics)

        return str(lyrics)
