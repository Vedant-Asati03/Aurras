"""
Core Player Module

This module provides the central player functionality for Aurras,
coordinating between online and offline playback modes.
"""

from aurras.player.online import ListenSongOnline
from aurras.player.offline import ListenSongOffline
from aurras.utils.exceptions import PlaybackError


class Player:
    """
    Central player class that coordinates playback functionality.

    This class serves as the main interface for playing music,
    delegating to the appropriate specialized player classes.
    """

    def __init__(self):
        """Initialize the Player class."""
        self._current_song = None
        self._is_playing = False

    def play_song(self, song_name, mode="online"):
        """
        Play a song using the specified mode.

        Args:
            song_name (str): Name of the song to play
            mode (str): Playback mode, either "online" or "offline"

        Returns:
            bool: True if playback started successfully

        Raises:
            PlaybackError: If playback cannot be started
        """
        self._current_song = song_name

        try:
            if mode == "online":
                player = ListenSongOnline(song_name)
                player.listen_song_online()
            elif mode == "offline":
                player = ListenSongOffline()
                # Implementation for offline playback
            else:
                raise PlaybackError(f"Unknown playback mode: {mode}")

            self._is_playing = True
            return True

        except Exception as e:
            self._is_playing = False
            raise PlaybackError(f"Failed to play {song_name}: {str(e)}")

    def stop(self):
        """Stop the current playback."""
        # Implementation for stopping playback
        self._is_playing = False

    @property
    def current_song(self):
        """Get the currently playing song."""
        return self._current_song

    @property
    def is_playing(self):
        """Check if a song is currently playing."""
        return self._is_playing
