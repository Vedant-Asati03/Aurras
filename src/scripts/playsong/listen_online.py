import sqlite3
from rich.table import Table

import config.config as path
from lib.searchsong import SearchSong
from src.scripts.playsong.mpv_player import MPVPlayer
from src.scripts.playlist.select_playlist_from_db import Select


class OnlineSongPlayer:
    """Base class for playing songs online."""

    def __init__(self):
        """Initialize the SongPlayer class."""
        self.config = path.Config()
        self.mpv_command = MPVPlayer()


class ListenSongOnline(OnlineSongPlayer):
    """
    A class for listening to a song online.

    Attributes:
        song_name (str): The name of the song to play.

    Methods:
        listen_song_online()
            Play the song online.
    """

    def __init__(self, song_user_searched: str):
        """
        Initialize the ListenSongOnline class.

        Args:
            song_name (str): The name of the song to play.
        """
        super().__init__()
        self.song_user_searched = song_user_searched
        self.search = SearchSong(self.song_user_searched)

    def _get_song_info(self):
        self.search.search_song()

    def listen_song_online(self):
        """Play the song online."""
        self._get_song_info()

        mpv_command = self.mpv_command.generate_mpv_command(
            self.search.song_url_searched
        )
        self.mpv_command.play(mpv_command, self.search.song_name_searched)


class ListenPlaylistOnline(OnlineSongPlayer):
    """
    A class for listening to a playlist online.

    Attributes:
        table (Table): An instance of the rich Table class.
        active_song (str): The currently active song in the playlist.
        queued_songs (list): List of queued songs in the playlist.

    Methods:
        _select_song_to_listen()
            Select a song to listen to from the list of songs in the active playlist.

        _queued_songs_in_playlist()
            Retrieve the queued songs in the active playlist.

        play_selected_playlist()
            Play the selected playlist.
    """

    def __init__(self):
        """Initialize the ListenPlaylistOnline class."""
        super().__init__()
        self.table = Table(show_header=False, header_style="bold magenta")
        self.queued_songs = []
        self.select_playlist = Select()

    def _queued_songs_in_playlist(self):
        """Retrieve the queued songs in the active playlist."""
        with sqlite3.connect(path.saved_playlists) as playlists:
            cursor = playlists.cursor()
            cursor.execute(
                f"SELECT playlists_songs FROM '{self.select_playlist.active_playlist}' WHERE id >= (SELECT id FROM '{self.select_playlist.active_playlist}' WHERE playlists_songs = (:song))",
                {"song": self.select_playlist.active_song},
            )
            queued_songs = (
                cursor.fetchall()
            )  # this is a list of tuples containing queued songs in active playlist

        self.queued_songs = [row[0] for row in queued_songs]

    def listen_playlist_online(self):
        """Play the selected playlist."""
        self.select_playlist.select_song_to_listen()
        self._queued_songs_in_playlist()

        for current_song in self.queued_songs:
            ListenSongOnline(current_song).listen_song_online()
