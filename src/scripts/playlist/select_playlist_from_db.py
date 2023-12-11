
import sqlite3
import questionary

from config import path
from lib.term_utils import clear_screen
from exceptions.exceptions import PlaylistNotFoundError


class Select:
    """
    Class for selecting playlist.
    """

    def __init__(self):
        """Initialize the SelectPlaylist class."""
        super().__init__()
        self.active_playlist = None
        self.songs_in_active_playlist = None
        self.active_song = None

    def select_playlist_from_db(self):
        """Select a playlist from the saved playlists."""
        with sqlite3.connect(path.saved_playlists) as playlists:
            cursor = playlists.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")

            tables = cursor.fetchall()
            table_names = [table[0] for table in tables]

            self.active_playlist = questionary.select(
                "Your Playlists\n\n", choices=table_names
            ).ask()

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

    def select_song_to_listen(self):
        """Select a song to listen to from the list of songs in the active playlist."""
        self.select_playlist_from_db()

        self.active_song = questionary.select(
            "Select a song to play",
            choices=self.songs_in_active_playlist,
        ).ask()

        clear_screen()
