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
from rich.text import Text
from rich.style import Style
from rich.logging import RichHandler
from rich import print as rprint
import logging

from ..utils.path_manager import PathManager

_path_manager = PathManager()

# Set up rich logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)],
)
log = logging.getLogger("aurras")

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
    MAX_HISTORY = 10000  # Maximum number of songs to keep in history
    DUPLICATE_TIMEFRAME = 30 * 60  # 30 minutes in seconds

    # Rich styles for consistent appearance
    TITLE_STYLE = Style(color="cyan", bold=True)
    SUCCESS_STYLE = Style(color="green")
    WARNING_STYLE = Style(color="yellow")
    ERROR_STYLE = Style(color="red", bold=True)
    INFO_STYLE = Style(color="blue")

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

    def _initialize_db(self):
        """Initialize the database for storing play history."""
        with console.status(
            "[bold blue]Initializing history database...", spinner="dots"
        ):
            with sqlite3.connect(_path_manager.history_db) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS play_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        song_name TEXT NOT NULL,
                        played_at INTEGER NOT NULL,
                        source TEXT,
                        play_count INTEGER DEFAULT 1
                    )
                """)
                conn.commit()

    def add_to_history(self, song_name: str, source: str = "search") -> None:
        """
        Add a song to the play history.

        Args:
            song_name: Name of the song
            source: Source of the song (e.g., 'search', 'playlist', 'offline')
        """
        # Directly check the database for the most recent entry to avoid relying on instance variable
        with sqlite3.connect(_path_manager.history_db) as conn:
            cursor = conn.cursor()

            # Get the most recently played song from the database with timestamp
            cursor.execute(
                "SELECT song_name, played_at, id, play_count FROM play_history ORDER BY played_at DESC LIMIT 1"
            )
            result = cursor.fetchone()

            current_time = int(time.time())

            if result:
                most_recent_song, played_at, song_id, play_count = result
                time_diff = current_time - played_at

                # If this song is the same as the most recently played one and within timeframe
                if (
                    most_recent_song == song_name
                    and time_diff <= self.DUPLICATE_TIMEFRAME
                ):
                    # Update the timestamp and increment play count
                    cursor.execute(
                        "UPDATE play_history SET played_at = ?, play_count = play_count + 1 WHERE id = ?",
                        (current_time, song_id),
                    )
                    log.info(
                        Text(
                            f"Updated play count for repeated: {song_name}",
                            style=self.INFO_STYLE,
                        )
                    )
                    conn.commit()
                    return

            # Add the new song to history
            cursor.execute(
                "INSERT INTO play_history (song_name, played_at, source, play_count) VALUES (?, ?, ?, ?)",
                (song_name, current_time, source, 1),
            )

            # Update the instance variable for quick checks in subsequent calls
            self._last_played_song = song_name

            # Reset navigation position when adding a new song
            self._current_position = -1

            # Trim history if it exceeds maximum size
            cursor.execute("SELECT COUNT(*) FROM play_history")
            count = cursor.fetchone()[0]

            if count > self.MAX_HISTORY:
                with console.status(
                    "[yellow]Trimming history database...", spinner="point"
                ):
                    # Delete oldest entries that exceed the limit
                    cursor.execute(
                        "DELETE FROM play_history WHERE id IN "
                        "(SELECT id FROM play_history ORDER BY played_at ASC LIMIT ?)",
                        (count - self.MAX_HISTORY,),
                    )
                    conn.commit()
                log.info(
                    Text("Trimmed history to maximum size", style=self.INFO_STYLE)
                )
            else:
                conn.commit()

            log.info(
                Text(f"Added to history: {song_name}", style=self.SUCCESS_STYLE)
            )

    def get_history_count(self) -> int:
        """Get the total number of songs in history."""
        with sqlite3.connect(_path_manager.history_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM play_history")
            return cursor.fetchone()[0]

    def get_recent_songs(self, limit: int = 10000) -> List[dict]:
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
                "SELECT id, song_name, played_at, source, play_count FROM play_history "
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
        log.debug(f"Current position in history: {self._current_position}")

        with sqlite3.connect(_path_manager.history_db) as conn:
            cursor = conn.cursor()

            # Get total number of songs in history
            cursor.execute("SELECT COUNT(*) FROM play_history")
            count = cursor.fetchone()[0]

            print(f" Total songs in history: {count}")

            if count <= 1:  # Need at least 2 songs to have a "previous" song
                print(" Not enough history to get previous song")
                return None

            # Move position back in history
            if self._current_position == -1:  # At the end (most recent)
                # Skip the current song (position 0) and go to the previous one (position 1)
                self._current_position = 1
            else:
                self._current_position = min(self._current_position + 1, count - 1)

            print(f" New position in history: {self._current_position}")

            # Get the song at the current position
            cursor.execute(
                "SELECT song_name FROM play_history "
                "ORDER BY played_at DESC LIMIT 1 OFFSET ?",
                (self._current_position,),
            )
            result = cursor.fetchone()

            if result:
                song_name = result[0]
                return song_name
            else:
                rprint(Text("No previous song found", style=self.WARNING_STYLE))
                return None

    def get_next_song(self) -> Optional[str]:
        """
        Get the next song from history (moving forward).

        Returns:
            The name of the next song, or None if at the end of history
        """
        log.debug(f"Current position in history for next: {self._current_position}")

        # If already at the end or no history navigation has occurred
        if self._current_position <= 0:
            self._current_position = -1
            print(" Already at most recent song")
            return None

        # Move position forward in history
        self._current_position -= 1
        print(f" New position for next: {self._current_position}")

        with sqlite3.connect(_path_manager.history_db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT song_name FROM play_history "
                "ORDER BY played_at DESC LIMIT 1 OFFSET ?",
                (self._current_position,),
            )
            result = cursor.fetchone()

            if result:
                song_name = result[0]
                return song_name
            else:
                rprint(Text("No next song found", style=self.WARNING_STYLE))
                return None

    def display_history(self) -> None:
        """Display the song play history in a formatted table."""
        with console.status("[bold blue]Loading history...", spinner="aesthetic"):
            recent_songs = self.get_recent_songs(20)  # Show up to 20 recent songs

        if not recent_songs:
            console.print(
                Panel(
                    "[italic]No song history found.[/italic]",
                    title="[bold]History[/bold]",
                    border_style="yellow",
                    title_align="center",
                    padding=(1, 2),
                )
            )
            return

        table = Table(
            title="[bold cyan]🎵 Recently Played Songs[/bold cyan]",
            box=ROUNDED,
            border_style="cyan",
            header_style="bold magenta",
            show_lines=True,
            title_style="bold cyan",
            caption="[dim italic]Your listening journey[/dim italic]",
            caption_style="dim italic",
            padding=(0, 1),
        )

        table.add_column("#", style="dim", justify="right")
        table.add_column("󰽱 Song", style="green bold")
        table.add_column(" Played", style="blue")
        table.add_column(" Source", style="magenta")
        table.add_column(" Count", style="yellow bold", justify="center")

        # Create alternate row styling
        styles = ["", "dim"]

        for i, song in enumerate(recent_songs, 1):
            # Format the timestamp
            timestamp = time.strftime(
                "%Y-%m-%d %H:%M", time.localtime(song["played_at"])
            )

            # Get play count, defaulting to 1 for older entries
            play_count = song.get("play_count", 1)

            # Style the count based on value
            if play_count > 5:
                count_display = f"[bold gold1]{play_count}[/bold gold1]"
            elif play_count > 1:
                count_display = f"[yellow]{play_count}[/yellow]"
            else:
                count_display = ""

            # Format source with emoji based on type
            source = song["source"]
            if source == "search":
                source_display = " search"
            elif source == "playlist":
                source_display = "󰲹 playlist"
            elif source == "offline":
                source_display = " offline"
            else:
                source_display = source

            # Add row with alternating style - Fix for empty style
            row_style = styles[i % 2]
            # Fix: Only add markup if there's an actual style
            row_num = f"[{row_style}]{i}[/{row_style}]" if row_style else str(i)

            table.add_row(
                row_num,
                song["song_name"],
                timestamp,
                source_display,
                count_display,
            )

        console.print(table)

        # Tips panel
        tips = Panel(
            "[cyan]Tip:[/cyan] Use [bold green]'b'[/bold green] key during playback to play previous song\n"
            "[cyan]Tip:[/cyan] Use [bold green]'n'[/bold green] key during playback to play next song",
            title="[bold]Navigation Tips[/bold]",
            border_style="dim blue",
            expand=False,
        )
        console.print(tips)

    def clear_history(self) -> None:
        """Clear the song play history."""
        with console.status(
            "[bold red]Clearing history database...", spinner="bouncingBar"
        ):
            with sqlite3.connect(_path_manager.history_db) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM play_history")
                conn.commit()

            self._current_position = -1
            self._last_played_song = None

        panel = Panel(
            "[bold green] Play history has been cleared successfully.[/bold green]",
            title="[bold]History Cleared[/bold]",
            border_style="green",
            padding=(1, 2),
        )
        console.print(panel)
