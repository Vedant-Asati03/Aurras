"""
Queue Manager Module

This module provides functionality for managing a queue of songs to be played.
"""

from typing import List, Optional
from rich.console import Console
from rich.table import Table
import threading

# Single instance queue across the application
_current_queue = []
_current_index = 0
_queue_lock = threading.RLock()
_queue_change_callbacks = []


class QueueManager:
    """
    A class for managing a queue of songs to play.

    This is implemented as a singleton to ensure the queue is accessible
    from anywhere in the application.
    """

    def __init__(self):
        """Initialize the QueueManager."""
        self.console = Console()

    def add_to_queue(self, songs: List[str]) -> None:
        """
        Add songs to the queue.

        Args:
            songs: List of song names to add to the queue
        """
        with _queue_lock:
            _current_queue.extend(songs)
            print(f">>> Queue after adding: {_current_queue}")
            self._notify_queue_changed()

    def clear_queue(self) -> None:
        """Clear the current queue."""
        with _queue_lock:
            global _current_queue, _current_index
            print(f">>> Queue before clearing: {_current_queue}")
            _current_queue = []
            _current_index = 0
            print(f">>> Queue after clearing: {_current_queue}")
            self._notify_queue_changed()

    def get_next_song(self) -> Optional[str]:
        """
        Get the next song in the queue.

        Returns:
            The next song name or None if queue is empty
        """
        with _queue_lock:
            global _current_index
            print(f">>> Queue state: {_current_queue}, index: {_current_index}")
            if _current_index >= len(_current_queue):
                print(">>> Queue is empty or index out of bounds")
                return None

            song = _current_queue[_current_index]
            _current_index += 1
            print(f">>> Got song from queue: {song}, new index: {_current_index}")
            return song

    def peek_next_song(self) -> Optional[str]:
        """
        Peek at the next song without removing it.

        Returns:
            The next song name or None if queue is empty
        """
        with _queue_lock:
            if _current_index >= len(_current_queue):
                return None
            return _current_queue[_current_index]

    def get_queue(self) -> List[str]:
        """
        Get all songs currently in the queue.

        Returns:
            List of songs in the queue
        """
        with _queue_lock:
            return _current_queue[_current_index:]

    def get_queue_position(self) -> int:
        """
        Get the current position in the queue.

        Returns:
            Current position in the queue
        """
        with _queue_lock:
            return _current_index

    def remove_from_queue(self, index: int) -> bool:
        """
        Remove a song from the queue by index.

        Args:
            index: Index of the song to remove (relative to current position)

        Returns:
            True if removed successfully, False otherwise
        """
        with _queue_lock:
            global _current_queue
            actual_index = _current_index + index

            if 0 <= actual_index < len(_current_queue):
                del _current_queue[actual_index]
                self._notify_queue_changed()
                return True
            return False

    def display_queue(self) -> None:
        """Display the current queue."""
        with _queue_lock:
            print(
                f">>> Raw queue data: {_current_queue}, current index: {_current_index}"
            )
            table = Table(title="Song Queue")
            table.add_column("#", style="dim")
            table.add_column("Song", style="green")

            upcoming = self.get_queue()
            if not upcoming:
                self.console.print("Queue is empty")
                return

            for i, song in enumerate(upcoming):
                table.add_row(str(i + 1), song)

            self.console.print(table)

    def register_change_callback(self, callback) -> None:
        """
        Register a callback to be called when the queue changes.

        Args:
            callback: Function to call when queue changes
        """
        _queue_change_callbacks.append(callback)

    def _notify_queue_changed(self) -> None:
        """Notify all registered callbacks that the queue has changed."""
        for callback in _queue_change_callbacks:
            try:
                callback()
            except Exception as e:
                self.console.print(f"Error in queue change callback: {e}")
