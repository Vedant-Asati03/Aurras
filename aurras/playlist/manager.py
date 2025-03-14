import sqlite3
import questionary

# Replace absolute import with relative import
from ..utils.path_manager import PathManager

_path_manager = PathManager()  # Create an instance to use

from ..utils.terminal import clear_screen
from ..utils.exceptions import PlaylistNotFoundError


class Select:
    """
    Class for selecting playlist.
    """

    def __init__(self):
        """Initialize the SelectPlaylist class."""
        self.active_playlist = None
        self.songs_in_active_playlist = None
        self.active_song = None

    def load_playlist_from_db(self):
        with sqlite3.connect(_path_manager.saved_playlists) as playlists:
            cursor = playlists.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")

            tables = cursor.fetchall()
            table_names = [table[0] for table in tables]

        return table_names

    def select_playlist_from_db(self):
        """Select a playlist from the saved playlists."""
        table_names = self.load_playlist_from_db()

        self.active_playlist = (
            questionary.select(
                "Your Playlists\n\n",
                choices=[playlist.capitalize() for playlist in table_names],
            )
            .ask()
            .lower()
        )

    def songs_from_active_playlist(self):
        with sqlite3.connect(_path_manager.saved_playlists) as playlists:
            cursor = playlists.cursor()

            cursor.execute(f"SELECT playlists_songs FROM '{self.active_playlist}'")
            songs_in_active_playlist = (
                cursor.fetchall()
            )  # this is a list of tuples containing all songs in active playlist

            if songs_in_active_playlist is not None:
                self.songs_in_active_playlist = [
                    str(song[0]) for song in songs_in_active_playlist
                ]
            else:
                raise PlaylistNotFoundError("Playlist Not Found!")

    def select_song_to_listen(self, playlist_name):
        """Select a song to listen to from the list of songs in the active playlist."""
        if playlist_name == "":
            self.select_playlist_from_db()
        else:
            self.active_playlist = playlist_name

        self.songs_from_active_playlist()

        self.active_song = questionary.select(
            "Select a song to play",
            choices=self.songs_in_active_playlist,
        ).ask()

        clear_screen()
