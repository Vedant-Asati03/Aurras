"""
History Manager Module

This module provides functionality for tracking and replaying recently played songs.
"""

import time
from typing import List, Optional

from aurras.utils.console import console
from aurras.utils.logger import get_logger
from aurras.utils.path_manager import _path_manager
from aurras.utils.db_connection import DatabaseConnectionManager

logger = get_logger("aurras.core.player.history", log_to_console=False)


class RecentlyPlayedManager:
    """
    A class for managing the history of recently played songs.

    This class provides functionality to:
    - Track songs as they are played
    - Retrieve recently played songs
    - Navigate through play history
    """

    _instance = None  # Singleton instance
    MAX_HISTORY = 500  # Maximum number of songs to keep in history
    DUPLICATE_TIMEFRAME = 30 * 60  # 30 minutes in seconds

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

        self._current_position = -1
        self._last_played_song = None
        # Use the DatabaseConnectionManager instead of direct sqlite3
        self._db_manager = DatabaseConnectionManager(_path_manager.history_db)
        self._initialize_db()
        self._initialized = True

    def __del__(self):
        """Clean up resources when the object is being destroyed."""
        self.close()

    def close(self):
        """Close the database connection."""
        if hasattr(self, "_db_manager"):
            self._db_manager.close()

    def _get_connection(self):
        """Get the database connection from the manager."""
        return self._db_manager.connection

    def _initialize_db(self):
        """Initialize the database for storing play history."""
        # Use context manager for automatic commit on success
        with self._db_manager as conn:
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

    def add_to_history(self, song_name: str, source: str = "search") -> None:
        """
        Add a song to the play history.

        Args:
            song_name: Name of the song
            source: Source of the song (e.g., 'search', 'playlist', 'offline')
        """
        current_time = int(time.time())

        # Use the database manager's connection within a context
        with self._db_manager as conn:
            cursor = conn.cursor()

            # Start transaction explicitly
            cursor.execute("BEGIN")

            try:
                # Check the most recent song (only one query)
                cursor.execute(
                    "SELECT song_name, played_at, id, play_count FROM play_history ORDER BY played_at DESC LIMIT 1"
                )
                result = cursor.fetchone()

                if result:
                    most_recent_song, played_at, song_id, play_count = result
                    time_diff = current_time - played_at

                    # If song is the same and within the timeframe, update
                    if (
                        most_recent_song == song_name
                        and time_diff <= self.DUPLICATE_TIMEFRAME
                    ):
                        cursor.execute(
                            "UPDATE play_history SET played_at = ?, play_count = play_count + 1 WHERE id = ?",
                            (current_time, song_id),
                        )
                        # Explicit commit needed here because we're returning early
                        conn.commit()
                        logger.info(f"Updated play count for repeated: {song_name}")
                        return

                # Add the new song to history
                cursor.execute(
                    "INSERT INTO play_history (song_name, played_at, source, play_count) VALUES (?, ?, ?, ?)",
                    (song_name, current_time, source, 1),
                )

                # Update the instance variable for navigation
                self._last_played_song = song_name
                self._current_position = -1

                # Trim history if necessary
                cursor.execute("SELECT COUNT(*) FROM play_history")
                count = cursor.fetchone()[0]

                if count > self.MAX_HISTORY:
                    cursor.execute(
                        "DELETE FROM play_history WHERE id IN "
                        "(SELECT id FROM play_history ORDER BY played_at ASC LIMIT ?)",
                        (count - self.MAX_HISTORY,),
                    )
                    logger.info("Trimmed history to maximum size")

                # Commit all changes
                conn.commit()
                logger.info(f"Added to history: {song_name}")

            except Exception as e:
                conn.rollback()
                logger.error(f"Error adding song to history: {e}")
                raise

    def get_history_count(self) -> int:
        """Get the total number of songs in history."""
        with self._db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM play_history")
            return cursor.fetchone()[0]

    def get_recent_songs(self, limit: int = 500) -> List[dict]:
        """
        Get the most recently played songs.

        Args:
            limit: Maximum number of songs to return

        Returns:
            List of dictionaries containing song details
        """
        # The DatabaseConnectionManager already sets row_factory = sqlite3.Row in get_connection()
        with self._db_manager as conn:
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
        logger.debug(f"Current position in history: {self._current_position}")

        with self._db_manager as conn:
            cursor = conn.cursor()

            # Get total number of songs in history
            cursor.execute("SELECT COUNT(*) FROM play_history")
            count = cursor.fetchone()[0]

            if count <= 1:  # Need at least 2 songs to have a "previous" song
                return None

            # Move position back in history
            if self._current_position == -1:  # At the end (most recent)
                # Skip the current song (position 0) and go to the previous one (position 1)
                self._current_position = 1
            else:
                self._current_position = min(self._current_position + 1, count - 1)

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
                console.print_warning(
                    "No previous songs found in your listening history."
                )
                return None

    def clear_history(self) -> None:
        """Clear the song play history."""
        with self._db_manager as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM play_history")

        self._current_position = -1
        self._last_played_song = None

        console.print_success("Listening history cleared successfully")
