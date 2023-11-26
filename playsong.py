"""
A module for playing and listening to songs online and offline.

This module provides classes for playing songs using an MPV player, listening to songs online,
and listening to playlists both online and offline.

Classes:
    - MPVPlayer: A class representing an MPV player for playing media files.
    - SongPlayer: A base class for playing songs online and offline.
    - ListenSongOnline: A class for listening to a song online.
    - ListenSongOffline: A class for listening to a song offline.
    - ListenPlaylistOnline: A class for listening to a playlist online.
    - ListenPlaylistOffline: A class for listening to a playlist offline.

Attributes:
    - path: A module-level configuration for file paths.

Note:
    - This module uses external modules such as rich, pytube, and sqlite3 for various functionalities.

Usage:
    - To use the classes in this module, import them into your script and create instances as needed.

"""

import sqlite3
import threading
import subprocess
from pathlib import Path

import questionary
from rich.table import Table
from rich.console import Console

import config as path
from config import Config
from lyrics import ShowLyrics, TranslateLyrics
from logger import debug_log
from mpvsetup import mpv_setup
from searchsong import SearchSong
from term_utils import clear_screen
from playlist import SelectPlaylist


class MPVPlayer:
    """
    A class representing an MPV player for playing media files.

    Attributes:
        console (Console): An instance of the rich Console class for console output.
        os_windows (bool): A boolean indicating whether the operating system is Windows.

    Methods:
        initialize_mpv()
            Initialize the MPV player by setting up the configuration files.

        generate_mpv_command(path_url: str) -> str:
            Generate an MPV command for the given path or URL.

        play(mpv_command: str)
            Play a media file using the MPV player.
    """

    def __init__(self):
        """
        Initialize the MPVPlayer class.
        """
        self.initialize_mpv()
        self.console = Console()
        self.os_windows = Path().anchor == "C:"

    def initialize_mpv(self):
        """
        Initialize mpv.conf and input.conf
        """
        mpv_setup()

    def generate_mpv_command(self, path_url: str):
        """Generate an MPV command for the given path or URL."""
        command = [
            "mpv",
            f"--include={path.mpv_conf}",
            f"--input-conf={path.input_conf}",
            path_url,
        ]

        return command

    def play(self, mpv_command: str):
        """
        Play a media file using the MPV player.

        Parameters:
            mpv_command (str): The command to play the media file with MPV.

        Raises:
            subprocess.CalledProcessError: If the MPV command execution fails.
        """
        subprocess.run(
            mpv_command,
            shell=bool(self.os_windows),
            check=True,
        )


class SongPlayer:
    """Base class for playing songs online and offline."""

    def __init__(self):
        """Initialize the SongPlayer class."""
        self.config = Config()
        self.console = Console()
        self.mpv_command = MPVPlayer()


class ListenSongOnline(SongPlayer):
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
        self.search.search_song()

    def listen_song_online(self):
        """Play the song online."""
        self.console.print(
            f"Listening - {self.search.song_name_searched}\n",
            end="\r",
            style="u #E8F3D6",
        )
        # TODO
        event = threading.Event()

        lyrics_translation = threading.Thread(
            target=TranslateLyrics(
                self.song_user_searched, self.search.song_name_searched, event
            ).translate_lyrics
        )

        lyrics = ShowLyrics(self.song_user_searched)
        lyrics.show_lyrics()
        lyrics_translation.start()
        mpv_command = self.mpv_command.generate_mpv_command(
            self.search.song_url_searched
        )
        MPVPlayer().play(mpv_command)

        event.set()
        clear_screen()


class ListenSongOffline(SongPlayer):
    """
    A class for listening to a song offline.

    Attributes:
        active_song (str): The currently active song.
        downloaded_songs (list): List of downloaded songs.
        mpv_command (str): The MPV command for playing the song.
        active_song_index (int): The index of the active song in the list.

    Methods:
        _select_song_to_listen()
            Select a song to listen to from the list of downloaded songs.

        listen_song_offline()
            Play the selected song offline.
    """

    def __init__(self):
        """Initialize the ListenSongOffline class."""
        super().__init__()
        self.active_song = None
        self.downloaded_songs = self.config.list_directory(path.downloaded_songs)

        self._select_song_to_listen()
        self.active_song_index = self.downloaded_songs.index(self.active_song)

    def _select_song_to_listen(self):
        """Select a song to listen to from the list of downloaded songs."""
        self.active_song = questionary.select(
            "Select a song to play\n", choices=self.downloaded_songs
        ).ask()
        clear_screen()

    def listen_song_offline(self):
        """Play the selected song offline."""
        for current_song in (self.downloaded_songs)[self.active_song_index :]:
            self.console.print(
                f"Playing🎶: {current_song}\n", end="\r", style="u #E8F3D6"
            )
            debug_log(f"playing offline song with command: {self.mpv_command}")
            mpv_command = self.mpv_command.generate_mpv_command(
                path.downloaded_songs / current_song
            )
            self.mpv_command.play(mpv_command)

            clear_screen()


class ListenPlaylistOnline(SongPlayer):
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
        self.active_song = None
        self.queued_songs = []
        self.select_playlist = SelectPlaylist()
        self.select_playlist.select_playlist_from_db()
        self._select_song_to_listen()
        self._queued_songs_in_playlist()

    def _select_song_to_listen(self):
        """Select a song to listen to from the list of songs in the active playlist."""
        self.active_song = questionary.select(
            "Select a song to play",
            choices=self.select_playlist.songs_in_active_playlist,
        ).ask()
        clear_screen()

    def _queued_songs_in_playlist(self):
        """Retrieve the queued songs in the active playlist."""
        with sqlite3.connect(path.saved_playlists) as playlists:
            cursor = playlists.cursor()
            cursor.execute(
                f"SELECT id FROM '{self.select_playlist.active_playlist}' WHERE playlists_songs = (:song)",
                {"song": self.active_song},
            )
            result = cursor.fetchone()
            active_song_index = result[0]
            cursor.execute(
                f"SELECT playlists_songs FROM '{self.select_playlist.active_playlist}' WHERE id >= ?",
                (active_song_index,),
            )
            queued_songs = (
                cursor.fetchall()
            )  # this is a list of tuples containing queued songs in active playlist

        self.queued_songs = [row[0] for row in queued_songs]

    def listen_playlist_online(self):
        """Play the selected playlist."""
        for current_song in self.queued_songs:
            ListenSongOnline(current_song).listen_song_online()
            clear_screen()


class ListenPlaylistOffline(SongPlayer):
    """
    A class for listening to a playlist offline.

    Attributes:
        downloaded_playlists (list): List of downloaded playlists.
        active_song (str): The currently active song in the playlist.
        active_playlist (str): The currently active playlist.
        mpv_command (str): The MPV command for playing the song.

    Methods:
        _select_playlist_to_listen()
            Select a downloaded playlist to listen to.

        _select_song_to_listen_from_playlist()
            Select a song to listen to from the downloaded playlist.

        listen_playlist_offline()
            Play the selected playlist offline.
    """

    def __init__(self):
        """Initialize the ListenPlaylistOffline class."""
        path.downloaded_playlists.mkdir(parents=True, exist_ok=True)

        super().__init__()
        self.downloaded_playlists = self.config.list_directory(
            path.downloaded_playlists
        )
        self.active_song = None
        self.active_playlist = None
        self.accessed_playlist = None
        self._select_playlist_to_listen()
        self._select_song_to_listen_from_playlist()

    def _select_playlist_to_listen(self):
        """Select a downloaded playlist to listen to."""
        self.active_playlist = questionary.select(
            "Your Downloaded Playlists", choices=self.downloaded_playlists
        ).ask()
        clear_screen()

    def _select_song_to_listen_from_playlist(self):
        """Select a song to listen to from the downloaded playlist."""
        self.accessed_playlist = path.downloaded_playlists / self.active_playlist
        self.accessed_playlist_directory_listed = self.config.list_directory(
            self.accessed_playlist
        )
        self.active_song = questionary.select(
            "Search: ", choices=self.accessed_playlist_directory_listed
        ).ask()
        clear_screen()

    def listen_playlist_offline(self):
        """Play the selected playlist offline."""
        active_song_index = self.accessed_playlist_directory_listed.index(
            self.active_song
        )

        for current_song in self.accessed_playlist_directory_listed[active_song_index:]:
            self.console.print(
                f"Playing🎶: {current_song}\n", end="\r", style="u #E8F3D6"
            )
            mpv_command = self.mpv_command.generate_mpv_command(
                path.downloaded_playlists / self.active_playlist / self.active_song
            )
            self.mpv_command.play(mpv_command)

            clear_screen()
