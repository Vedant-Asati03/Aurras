from pathlib import Path
import questionary
from rich.console import Console

# Replace absolute import with relative import
from ..utils.path_manager import PathManager

_path_manager = PathManager()

from ..utils.logger import debug_log
from ..utils.terminal import clear_screen
from ..utils.exceptions import PlaylistNotFoundError, SongsNotFoundError
from ..player.mpv import MPVPlayer
from ..player.history import RecentlyPlayedManager


class OfflineSongPlayer:
    """Base class for playing songs offline."""

    def __init__(self):
        """Initialize the SongPlayer class."""
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
        self.downloaded_songs_list = _path_manager.list_directory(
            _path_manager.downloaded_songs_dir
        )

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
                Path(_path_manager.downloaded_songs_dir, current_song)
            )

            # Add to play history before playing
            history_manager = RecentlyPlayedManager()
            history_manager.add_to_history(current_song, "offline")

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
        _path_manager.playlists_dir.mkdir(parents=True, exist_ok=True)

        super().__init__()
        self.active_song = None
        self.active_playlist = None
        self.accessed_playlist = None
        self.downloaded_playlists = None
        self.accessed_playlist_directory_listed = None

    def _select_playlist_to_listen(self):
        """Select a downloaded playlist to listen to."""
        self.downloaded_playlists = _path_manager.list_directory(
            _path_manager.playlists_dir
        )
        if self.downloaded_playlists is None:
            raise PlaylistNotFoundError("Playlist Not Found!")

        self.active_playlist = questionary.select(
            "Your Downloaded Playlists", choices=self.downloaded_playlists
        ).ask()
        clear_screen()

    def _select_song_to_listen_from_playlist(self):
        """Select a song to listen to from the downloaded playlist."""
        self.accessed_playlist = _path_manager.playlists_dir / self.active_playlist
        self.accessed_playlist_directory_listed = _path_manager.list_directory(
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
                _path_manager.playlists_dir / self.active_playlist / self.active_song
            )

            # Add to play history before playing
            history_manager = RecentlyPlayedManager()
            history_manager.add_to_history(
                current_song, f"playlist:{self.active_playlist}"
            )

            self.mpv_command.play(mpv_command, current_song)
