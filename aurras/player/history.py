"""
History Manager Module

This module provides functionality for tracking and replaying recently played songs.
"""

import sqlite3
import time
from typing import List, Optional
from rich.console import Console
from rich.table import Table
from rich.box import ROUNDED
from rich.panel import Panel
from rich import print as rprint

from ..utils.path_manager import PathManager

_path_manager = PathManager()

# Create a global console for consistent styling
console = Console()


class RecentlyPlayedManager:
    """
    A class for managing the history of recently played songs.

    This class provides functionality to:
    - Track songs as they are played
    - Retrieve recently played songs
    - Navigate through play history
    """

    _instance = None  # Singleton instance
    MAX_HISTORY = 100  # Maximum number of songs to keep in history

    def __new__(cls):
        """Ensure singleton pattern - only one instance of history manager exists."""
        if cls._instance is None:
            cls._instance = super(RecentlyPlayedManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the RecentlyPlayedManager."""
        # Only initialize once due to singleton pattern
        if getattr(self, "_initialized", False):
            return

        self.console = Console()
        self._current_position = -1
        self._last_played_song = None
        self._initialize_db()
        self._initialized = True
        print(">>> History manager initialized")

    def _initialize_db(self):
        """Initialize the database for storing play history."""
        with sqlite3.connect(_path_manager.history_db) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS play_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    song_name TEXT NOT NULL,
                    played_at INTEGER NOT NULL,
                    source TEXT
                )
            """)
            conn.commit()

    def add_to_history(self, song_name: str, source: str = "search") -> None:
        """
        Add a song to the play history.

        Args:
            song_name: The name of the song that was played
            source: Where the song came from (search, playlist, etc.)
        """
        # Skip if it's the same song being played again right away
        if self._last_played_song == song_name:
            print(f">>> Skipping duplicate history entry for: {song_name}")
            return

        self._last_played_song = song_name
        print(f">>> Adding to history: {song_name} (source: {source})")

        with sqlite3.connect(_path_manager.history_db) as conn:
            cursor = conn.cursor()

            # Add the new song to history
            timestamp = int(time.time())
            cursor.execute(
                "INSERT INTO play_history (song_name, played_at, source) VALUES (?, ?, ?)",
                (song_name, timestamp, source),
            )

            # Reset current position to the end (most recent)
            self._current_position = -1

            # Trim history if it exceeds maximum size
            cursor.execute("SELECT COUNT(*) FROM play_history")
            count = cursor.fetchone()[0]

            if count > self.MAX_HISTORY:
                # Delete oldest entries that exceed the limit
                cursor.execute(
                    "DELETE FROM play_history WHERE id IN "
                    "(SELECT id FROM play_history ORDER BY played_at ASC LIMIT ?)",
                    (count - self.MAX_HISTORY,),
                )

            conn.commit()

    def get_history_count(self) -> int:
        """Get the total number of songs in history."""
        with sqlite3.connect(_path_manager.history_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM play_history")
            return cursor.fetchone()[0]

    def get_recent_songs(self, limit: int = 10) -> List[dict]:
        """
        Get the most recently played songs.

        Args:
            limit: Maximum number of songs to return

        Returns:
            List of dictionaries containing song details
        """
        with sqlite3.connect(_path_manager.history_db) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, song_name, played_at, source FROM play_history "
                "ORDER BY played_at DESC LIMIT ?",
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_previous_song(self) -> Optional[str]:
        """
        Get the previous song from history.

        Returns:
            The name of the previous song, or None if at the beginning of history
        """
        print(f">>> Current position in history: {self._current_position}")

        with sqlite3.connect(_path_manager.history_db) as conn:
            cursor = conn.cursor()

            # Get total number of songs in history
            cursor.execute("SELECT COUNT(*) FROM play_history")
            count = cursor.fetchone()[0]

            print(f">>> Total songs in history: {count}")

            if count <= 1:  # Need at least 2 songs to have a "previous" song
                print(">>> Not enough history to get previous song")
                return None

            # Move position back in history
            if self._current_position == -1:  # At the end (most recent)
                # Skip the current song (position 0) and go to the previous one (position 1)
                self._current_position = 1
            else:
                self._current_position = min(self._current_position + 1, count - 1)

            print(f">>> New position in history: {self._current_position}")

            # Get the song at the current position
            cursor.execute(
                "SELECT song_name FROM play_history "
                "ORDER BY played_at DESC LIMIT 1 OFFSET ?",
                (self._current_position,),
            )
            result = cursor.fetchone()

            if result:
                print(f">>> Previous song found: {result[0]}")
                return result[0]
            else:
                print(">>> No previous song found")
                return None

    def get_next_song(self) -> Optional[str]:
        """
        Get the next song from history (moving forward).

        Returns:
            The name of the next song, or None if at the end of history
        """
        print(f">>> Current position in history for next: {self._current_position}")

        # If already at the end or no history navigation has occurred
        if self._current_position <= 0:
            self._current_position = -1
            print(">>> Already at most recent song")
            return None

        # Move position forward in history
        self._current_position -= 1
        print(f">>> New position for next: {self._current_position}")

        with sqlite3.connect(_path_manager.history_db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT song_name FROM play_history "
                "ORDER BY played_at DESC LIMIT 1 OFFSET ?",
                (self._current_position,),
            )
            result = cursor.fetchone()

            if result:
                print(f">>> Next song found: {result[0]}")
                return result[0]
            else:
                print(">>> No next song found")
                return None

    def display_history(self) -> None:
        """Display the song play history in a formatted table."""
        recent_songs = self.get_recent_songs(20)  # Show up to 20 recent songs

        if not recent_songs:
            console.print(
                Panel(
                    "[italic]No song history found.[/italic]",
                    title="History",
                    border_style="yellow",
                )
            )
            return

        table = Table(
            title="🎵 Recently Played Songs",
            box=ROUNDED,
            border_style="cyan",
            header_style="bold magenta",
        )
        table.add_column("#", style="dim")
        table.add_column("Song", style="green")
        table.add_column("Played", style="blue")
        table.add_column("Source", style="magenta")

        for i, song in enumerate(recent_songs, 1):
            # Format the timestamp
            timestamp = time.strftime(
                "%Y-%m-%d %H:%M", time.localtime(song["played_at"])
            )
            table.add_row(str(i), song["song_name"], timestamp, song["source"])

        console.print(table)
        console.print(
            "[dim]Tip: Use 'b' key during playback to play previous song[/dim]"
        )

    def clear_history(self) -> None:
        """Clear the song play history."""
        with sqlite3.connect(_path_manager.history_db) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM play_history")
            conn.commit()

        self._current_position = -1
        self._last_played_song = None
        self.console.print("Play history cleared.")
