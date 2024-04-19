from pathlib import Path
import questionary
from rich.console import Console

from config import path
from lib.logger import debug_log
from lib.term_utils import clear_screen
from exceptions.exceptions import PlaylistNotFoundError, SongsNotFoundError
from .mpv_player import MPVPlayer


class OfflineSongPlayer:
    """Base class for playing songs offline."""

    def __init__(self):
        """Initialize the SongPlayer class."""
        self.config = path.Config()
        self.console = Console()
        self.mpv_command = MPVPlayer()


class ListenSongOffline(OfflineSongPlayer):
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
        self.downloaded_songs_list = None
        self.active_song_index = None

    def _get_songs_list_listen(self):
        self.downloaded_songs_list = self.config.list_directory(path.downloaded_songs)

    def _select_song_to_listen(self):
        """Select a song to listen to from the list of downloaded songs."""
        self._get_songs_list_listen()

        if self.downloaded_songs_list is None:
            raise SongsNotFoundError("Downloaded Songs Not Found!")
        self.active_song = questionary.select(
            "Select a song to play\n", choices=self.downloaded_songs_list
        ).ask()

        self.active_song_index = self.downloaded_songs_list.index(self.active_song)
        clear_screen()

    def listen_song_offline(self):
        """Play the selected song offline."""
        self._select_song_to_listen()

        for current_song in (self.downloaded_songs_list)[self.active_song_index :]:
            debug_log(f"playing offline song with command: {self.mpv_command}")
            mpv_command = self.mpv_command.generate_mpv_command(
                Path(path.downloaded_songs, current_song)
            )
            self.mpv_command.play(mpv_command, current_song)


class ListenPlaylistOffline(OfflineSongPlayer):
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
        self.active_song = None
        self.active_playlist = None
        self.accessed_playlist = None
        self.downloaded_playlists = None
        self.accessed_playlist_directory_listed = None

    def _select_playlist_to_listen(self):
        """Select a downloaded playlist to listen to."""
        self.downloaded_playlists = self.config.list_directory(
            path.downloaded_playlists
        )
        if self.downloaded_playlists is None:
            raise PlaylistNotFoundError("Playlist Not Found!")

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

    def listen_playlist_offline(self, playlist_name=""):
        """Play the selected playlist offline."""
        if playlist_name == "":
            self._select_playlist_to_listen()
        else:
            self.active_playlist = playlist_name

        self._select_song_to_listen_from_playlist()

        active_song_index = self.accessed_playlist_directory_listed.index(
            self.active_song
        )

        for current_song in self.accessed_playlist_directory_listed[active_song_index:]:
            mpv_command = self.mpv_command.generate_mpv_command(
                path.downloaded_playlists / self.active_playlist / self.active_song
            )
            self.mpv_command.play(mpv_command, current_song)
