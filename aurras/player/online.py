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

    def _get_song_info(self):
        """Search for the song and get its metadata."""
        self.search.search_song()

    def listen_song_online(self):
        """Play the song online by streaming it."""
        self._get_song_info()

        mpv_command = self.mpv_command.generate_mpv_command(
            self.search.song_url_searched
        )
        self.mpv_command.play(mpv_command, self.search.song_name_searched)


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
