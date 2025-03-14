"""
Online Player Module

This module provides functionality for playing songs online by streaming.
"""

import sqlite3
from rich.table import Table

# Replace absolute import with relative import
from ..utils.path_manager import PathManager

_path_manager = PathManager()

from ..utils.config import Config
from ..services.youtube.search import SearchSong
from ..player.mpv import MPVPlayer
from ..playlist.manager import Select
from ..player.queue import QueueManager
from ..player.history import RecentlyPlayedManager


class OnlineSongPlayer:
    """Base class for playing songs online."""

    def __init__(self):
        """Initialize the SongPlayer class."""
        self.config = Config()
        self.mpv_command = MPVPlayer()


class ListenSongOnline(OnlineSongPlayer):
    """
    A class for listening to a song online.

    Attributes:
        song_user_searched (str): The name of the song to search and play.

    Methods:
        listen_song_online(): Play the song online.
    """

    def __init__(self, song_user_searched: str):
        """
        Initialize the ListenSongOnline class.

        Args:
            song_user_searched (str): The name of the song to search and play.
        """
        super().__init__()
        self.search = SearchSong(song_user_searched)
        self.queue_manager = QueueManager()
        self._is_part_of_queue = False

    def _get_song_info(self):
        """Search for the song and get its metadata."""
        print(f">>> Searching for song: {self.search.song_user_searched}")
        self.search.search_song()
        print(f">>> Found song: {self.search.song_name_searched}")

    def listen_song_online(self):
        """Play the song online by streaming it."""
        try:
            self._get_song_info()

            print(f">>> Generating command to play: {self.search.song_name_searched}")
            mpv_command = self.mpv_command.generate_mpv_command(
                self.search.song_url_searched
            )

            print(f">>> Starting playback for: {self.search.song_name_searched}")

            # Create history manager
            history_manager = RecentlyPlayedManager()

            # Add to play history before playing
            # Only add if not called from previous/next navigation
            if not getattr(self, "_navigating_history", False):
                history_manager.add_to_history(self.search.song_name_searched, "online")

            # Play and get the exit code
            exit_code = self.mpv_command.play(
                mpv_command, self.search.song_name_searched
            )
            print(f">>> Song finished playing (exit code: {exit_code})")

            # Handle the exit code to determine what to do next
            if exit_code == 10:  # Previous song (b key)
                print(">>> User requested previous song")
                prev_song = history_manager.get_previous_song()
                if prev_song and prev_song != self.search.song_name_searched:
                    print(f">>> Playing previous song: {prev_song}")
                    player = ListenSongOnline(prev_song)
                    player._navigating_history = True  # Mark as navigating
                    player._is_part_of_queue = True
                    player.listen_song_online()
                else:
                    print(">>> No previous song in history different from current")

                # Return early to prevent further queue processing
                return

            elif exit_code == 11:  # Next song (n key)
                print(">>> User requested next song")
                next_song = history_manager.get_next_song()
                if next_song:
                    print(f">>> Playing next song in history: {next_song}")
                    player = ListenSongOnline(next_song)
                    player._navigating_history = True  # Mark as navigating
                    player._is_part_of_queue = True
                    player.listen_song_online()
                    return
                # Let the normal queue processing continue below if no next in history
                print(">>> No next song in history, checking queue")

            # Normal queue processing
            next_song = self.queue_manager.get_next_song()
            if next_song:
                print(f"\n>>> Playing next song in queue: {next_song}")
                next_player = ListenSongOnline(next_song)
                next_player._is_part_of_queue = True
                try:
                    next_player.listen_song_online()
                except Exception as e:
                    print(f">>> Error playing next song: {e}")
                    # Continue to the next song in queue even if this one fails
                    another_song = self.queue_manager.get_next_song()
                    if another_song:
                        ListenSongOnline(another_song).listen_song_online()
            else:
                print(">>> No more songs in queue")

        except Exception as e:
            print(f">>> Error playing song: {e}")
            if not self._is_part_of_queue:
                next_song = self.queue_manager.get_next_song()
                if next_song:
                    print(f"\n>>> Skipping to next song in queue: {next_song}")
                    next_player = ListenSongOnline(next_song)
                    next_player._is_part_of_queue = True
                    next_player.listen_song_online()


def play_song_sequence(songs: list):
    """
    Play a sequence of songs.

    Args:
        songs: List of song names to play
    """
    if not songs:
        print(">>> No songs provided to play")
        return

    queue_manager = QueueManager()

    # Clear any existing queue first to avoid conflicts
    print(">>> Clearing any existing queue")
    queue_manager.clear_queue()

    # Add all songs to the queue
    print(f">>> Adding {len(songs)} songs to queue")
    queue_manager.add_to_queue(songs)

    # Display current queue state
    print(">>> Current queue state:")
    queue_manager.display_queue()

    # Print queue information
    print(f"\n>>> Added {len(songs)} songs to queue:")
    for i, song in enumerate(songs):
        print(f"  {i + 1}. {song}")
    print()

    # Start playing the first song
    first_song = queue_manager.get_next_song()
    if first_song:
        print(f">>> Now playing: {first_song}")
        player = ListenSongOnline(first_song)
        player._is_part_of_queue = True
        player.listen_song_online()
    else:
        print(">>> Queue is empty, nothing to play")


class ListenPlaylistOnline(OnlineSongPlayer):
    """
    A class for listening to a playlist online.

    Attributes:
        table (Table): Rich table for displaying playlist information.
        queued_songs (list): List of queued songs in the playlist.
        select_playlist (PlaylistSelector): Playlist selection utility.
    """

    def __init__(self):
        """Initialize the ListenPlaylistOnline class."""
        super().__init__()
        self.table = Table(show_header=False, header_style="bold magenta")
        self.queued_songs = []
        self.select_playlist = Select()
        self.path_manager = PathManager()

    def _queued_songs_in_playlist(self):
        """Retrieve the queued songs in the active playlist."""
        with sqlite3.connect(self.path_manager.saved_playlists) as playlists:
            cursor = playlists.cursor()
            cursor.execute(
                f"SELECT playlists_songs FROM '{self.select_playlist.active_playlist}' WHERE id >= (SELECT id FROM '{self.select_playlist.active_playlist}' WHERE playlists_songs = (:song))",
                {"song": self.select_playlist.active_song},
            )
            queued_songs = cursor.fetchall()

        self.queued_songs = [row[0] for row in queued_songs]

    def listen_playlist_online(self, playlist_name=""):
        """
        Play the selected playlist.

        Args:
            playlist_name (str): Optional name of the playlist to play.
                                If not provided, user will be prompted to select.
        """
        self.select_playlist.select_song_to_listen(playlist_name)
        self._queued_songs_in_playlist()

        for current_song in self.queued_songs:
            ListenSongOnline(current_song).listen_song_online()
