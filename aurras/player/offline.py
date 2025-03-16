from pathlib import Path
import questionary
from rich.console import Console
import random
from rich.table import Table
from rich.box import ROUNDED

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

    def listen_playlist_offline(self, playlist_name="", shuffle=False):
        """Play the selected playlist offline.

        Args:
            playlist_name (str): Optional name of the playlist to play
            shuffle (bool): Whether to shuffle the playlist
        """
        try:
            if playlist_name == "":
                self._select_playlist_to_listen()
            else:
                # Verify the specified playlist exists
                available_playlists = _path_manager.list_directory(
                    _path_manager.playlists_dir
                )
                if available_playlists and playlist_name in available_playlists:
                    self.active_playlist = playlist_name
                else:
                    self.console.print(
                        f"[bold red]Playlist '{playlist_name}' not found![/bold red]"
                    )
                    self._select_playlist_to_listen()

            # Verify active playlist is set
            if not self.active_playlist:
                self.console.print("[bold red]No playlist selected.[/bold red]")
                return

            # Get songs from the playlist
            self._select_song_to_listen_from_playlist()

            # Verify active song is set
            if not self.active_song:
                self.console.print(
                    f"[bold red]No song selected from playlist '{self.active_playlist}'.[/bold red]"
                )
                return

            # Get all songs from the accessed playlist directory
            songs = self.accessed_playlist_directory_listed.copy()

            if not songs:
                self.console.print(
                    f"[yellow]Playlist '{self.active_playlist}' is empty.[/yellow]"
                )
                return

            # Find the index of the active song
            active_song_index = songs.index(self.active_song)

            # Get only songs from the active song onwards
            songs_to_play = songs[active_song_index:]

            if shuffle:
                # Shuffle the songs
                random.shuffle(songs_to_play)

                # Create a nice table to show the shuffled playlist
                shuffle_table = Table(
                    title="🎲 Shuffled Playlist", box=ROUNDED, border_style="#D09CFA"
                )
                shuffle_table.add_column("#", style="dim")
                shuffle_table.add_column("Song", style="#D7C3F1")

                for i, song in enumerate(songs_to_play, 1):
                    shuffle_table.add_row(str(i), song)

                self.console.print(shuffle_table)

            # Play each song
            for current_song in songs_to_play:
                try:
                    playlist_path = _path_manager.playlists_dir / self.active_playlist
                    song_path = playlist_path / current_song

                    if not song_path.exists():
                        self.console.print(
                            f"[yellow]Song file not found: {song_path}[/yellow]"
                        )
                        continue

                    mpv_command = self.mpv_command.generate_mpv_command(song_path)

                    # Add to play history before playing
                    history_manager = RecentlyPlayedManager()
                    history_manager.add_to_history(
                        current_song, f"playlist:{self.active_playlist}"
                    )

                    self.mpv_command.play(mpv_command, current_song)
                except Exception as e:
                    self.console.print(
                        f"[bold red]Error playing '{current_song}': {str(e)}[/bold red]"
                    )
                    # Continue with next song
                    continue

        except Exception as e:
            self.console.print(f"[bold red]Error playing playlist: {str(e)}[/bold red]")
