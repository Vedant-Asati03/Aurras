"""
Autoplay Module

This module provides functionality for automatically playing songs.
"""

import threading
import time
from queue import Queue

from aurras.utils.logger import debug_log


class AutoPlayManager:
    """
    Class for managing the autoplay of songs.
    """

    def __init__(self):
        """Initialize the AutoPlayManager class."""
        self.queue = Queue()
        self.current_song = None
        self.playing = False
        self.play_thread = None

    def add_song(self, song):
        """
        Add a song to the autoplay queue.

        Args:
            song (str): The song to add to the queue
        """
        self.queue.put(song)
        debug_log(f"Added song to queue: {song}")

    def auto_play(self, play_function):
        """
        Start autoplay of songs in the queue.

        Args:
            play_function (callable): A function that plays a song when called with a song name
        """
        self.playing = True
        self.play_thread = threading.Thread(
            target=self._play_thread, args=(play_function,), daemon=True
        )
        self.play_thread.start()

    def _play_thread(self, play_function):
        """
        Thread function for playing songs from the queue.

        Args:
            play_function (callable): A function that plays a song when called with a song name
        """
        while self.playing:
            if not self.queue.empty():
                song = self.queue.get()
                self.current_song = song
                debug_log(f"Auto-playing song: {song}")
                try:
                    play_function(song)
                except Exception as e:
                    debug_log(f"Error playing song {song}: {str(e)}")
            else:
                time.sleep(0.5)

    def stop(self):
        """Stop the autoplay."""
        self.playing = False
        if self.play_thread and self.play_thread.is_alive():
            self.play_thread.join(timeout=1.0)
            debug_log("Stopped autoplay")


def auto_play(queued_song: str):
    """
    Legacy function for backward compatibility.

    Args:
        queued_song (str): Song to auto-play
    """
    manager = AutoPlayManager()
    manager.add_song(queued_song)
    # This is a placeholder implementation
    # In a real scenario, you'd need to provide a play function
    pass
