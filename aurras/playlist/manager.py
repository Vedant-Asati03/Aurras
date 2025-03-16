import sqlite3
import questionary
import random
from rich.console import Console
from rich.table import Table
from rich.box import ROUNDED

# Replace absolute import with relative import
from ..utils.path_manager import PathManager

_path_manager = PathManager()  # Create an instance to use

from ..utils.terminal import clear_screen
from ..utils.exceptions import PlaylistNotFoundError


class Select:
    """
    Class for selecting and managing playlists.
    """

    def __init__(self):
        """Initialize the SelectPlaylist class."""
        self.active_playlist = None
        self.songs_in_active_playlist = None
        self.active_song = None
        self.console = Console()

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

        if not table_names:
            self.console.print(
                "[bold red]No playlists found. Please import or create a playlist first.[/bold red]"
            )
            return

        # Convert table names to display format and back for better UX
        display_choices = [playlist.capitalize() for playlist in table_names]

        selected = questionary.select(
            "Your Playlists\n\n",
            choices=display_choices,
        ).ask()

        if selected is None:
            self.console.print("[yellow]Playlist selection cancelled.[/yellow]")
            return

        # Convert back to lowercase for database operations
        self.active_playlist = selected.lower()

    def songs_from_active_playlist(self):
        """Get all songs from the active playlist."""
        if not self.active_playlist:
            self.console.print("[bold red]No playlist selected.[/bold red]")
            self.songs_in_active_playlist = []
            return

        try:
            with sqlite3.connect(_path_manager.saved_playlists) as playlists:
                cursor = playlists.cursor()

                # Verify the playlist table exists
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (self.active_playlist,),
                )
                if not cursor.fetchone():
                    self.console.print(
                        f"[bold red]Playlist '{self.active_playlist}' not found in database.[/bold red]"
                    )
                    self.songs_in_active_playlist = []
                    return

                # Get the songs
                cursor.execute(f"SELECT playlists_songs FROM '{self.active_playlist}'")
                songs_in_active_playlist = cursor.fetchall()

                if songs_in_active_playlist:
                    self.songs_in_active_playlist = [
                        str(song[0]) for song in songs_in_active_playlist
                    ]
                else:
                    self.console.print(
                        f"[yellow]Playlist '{self.active_playlist}' is empty.[/yellow]"
                    )
                    self.songs_in_active_playlist = []
        except sqlite3.Error as e:
            self.console.print(f"[bold red]Database error: {str(e)}[/bold red]")
            self.songs_in_active_playlist = []

    def select_song_to_listen(self, playlist_name):
        """Select a song to listen to from the list of songs in the active playlist."""
        if playlist_name == "":
            self.select_playlist_from_db()
        else:
            # Validate the playlist exists
            with sqlite3.connect(_path_manager.saved_playlists) as playlists:
                cursor = playlists.cursor()
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (playlist_name.lower(),),
                )
                if cursor.fetchone():
                    self.active_playlist = playlist_name.lower()
                else:
                    self.console.print(
                        f"[bold red]Playlist '{playlist_name}' not found.[/bold red]"
                    )
                    self.select_playlist_from_db()

        # Make sure a playlist was selected
        if not self.active_playlist:
            return

        self.songs_from_active_playlist()

        # Make sure there are songs in the playlist
        if not self.songs_in_active_playlist:
            self.console.print(
                f"[bold red]No songs found in playlist '{self.active_playlist}'.[/bold red]"
            )
            return

        selected = questionary.select(
            "Select a song to play",
            choices=self.songs_in_active_playlist,
        ).ask()

        if selected is None:
            self.console.print("[yellow]Song selection cancelled.[/yellow]")
            return

        self.active_song = selected
        clear_screen()

    def add_song_to_playlist(self, playlist_name, song_name):
        """Add a song to an existing playlist.

        Args:
            playlist_name (str): Name of the playlist
            song_name (str): Name of the song to add
        """
        if playlist_name == "":
            self.select_playlist_from_db()
        else:
            self.active_playlist = playlist_name

        with sqlite3.connect(_path_manager.saved_playlists) as playlists:
            cursor = playlists.cursor()
            try:
                # Check if song already exists in playlist
                cursor.execute(
                    f"SELECT COUNT(*) FROM '{self.active_playlist}' WHERE playlists_songs = ?",
                    (song_name,),
                )
                if cursor.fetchone()[0] > 0:
                    self.console.print(
                        f"[yellow]Song '{song_name}' already exists in playlist[/yellow]"
                    )
                    return False

                # Add the song
                cursor.execute(
                    f"INSERT INTO '{self.active_playlist}' (playlists_songs) VALUES (?)",
                    (song_name,),
                )
                self.console.print(
                    f"[green]Added '{song_name}' to playlist '{self.active_playlist}'[/green]"
                )
                return True
            except Exception as e:
                self.console.print(f"[bold red]Error adding song: {str(e)}[/bold red]")
                return False

    def remove_song_from_playlist(self, playlist_name="", song_name=""):
        """Remove a song from a playlist.

        Args:
            playlist_name (str): Name of the playlist
            song_name (str): Name of the song to remove
        """
        if playlist_name == "":
            self.select_playlist_from_db()
        else:
            self.active_playlist = playlist_name

        self.songs_from_active_playlist()

        if song_name == "":
            song_name = questionary.select(
                "Select a song to remove", choices=self.songs_in_active_playlist
            ).ask()

        with sqlite3.connect(_path_manager.saved_playlists) as playlists:
            cursor = playlists.cursor()
            cursor.execute(
                f"DELETE FROM '{self.active_playlist}' WHERE playlists_songs = ?",
                (song_name,),
            )
            if cursor.rowcount > 0:
                self.console.print(
                    f"[green]Removed '{song_name}' from playlist '{self.active_playlist}'[/green]"
                )
                return True
            else:
                self.console.print(
                    f"[yellow]Song '{song_name}' not found in playlist[/yellow]"
                )
                return False

    def move_song_in_playlist(self, playlist_name="", song_name="", direction="up"):
        """Move a song up or down within a playlist.

        Args:
            playlist_name (str): Name of the playlist
            song_name (str): Name of the song to move
            direction (str): Direction to move the song ('up' or 'down')
        """
        if playlist_name == "":
            self.select_playlist_from_db()
        else:
            self.active_playlist = playlist_name

        self.songs_from_active_playlist()

        if song_name == "":
            song_name = questionary.select(
                "Select a song to move", choices=self.songs_in_active_playlist
            ).ask()

        if song_name not in self.songs_in_active_playlist:
            self.console.print(
                f"[yellow]Song '{song_name}' not found in playlist[/yellow]"
            )
            return False

        song_index = self.songs_in_active_playlist.index(song_name)

        if direction == "up" and song_index > 0:
            # Swap with the song above
            with sqlite3.connect(_path_manager.saved_playlists) as playlists:
                cursor = playlists.cursor()
                # Get IDs of both songs
                cursor.execute(
                    f"SELECT id FROM '{self.active_playlist}' WHERE playlists_songs = ?",
                    (song_name,),
                )
                current_id = cursor.fetchone()[0]

                cursor.execute(
                    f"SELECT id FROM '{self.active_playlist}' WHERE playlists_songs = ?",
                    (self.songs_in_active_playlist[song_index - 1],),
                )
                other_id = cursor.fetchone()[0]

                # Swap their positions
                cursor.execute(
                    f"UPDATE '{self.active_playlist}' SET playlists_songs = ? WHERE id = ?",
                    (self.songs_in_active_playlist[song_index - 1], current_id),
                )
                cursor.execute(
                    f"UPDATE '{self.active_playlist}' SET playlists_songs = ? WHERE id = ?",
                    (song_name, other_id),
                )
                self.console.print(f"[green]Moved '{song_name}' up in playlist[/green]")
                return True

        elif (
            direction == "down" and song_index < len(self.songs_in_active_playlist) - 1
        ):
            # Swap with the song below
            with sqlite3.connect(_path_manager.saved_playlists) as playlists:
                cursor = playlists.cursor()
                # Get IDs of both songs
                cursor.execute(
                    f"SELECT id FROM '{self.active_playlist}' WHERE playlists_songs = ?",
                    (song_name,),
                )
                current_id = cursor.fetchone()[0]

                cursor.execute(
                    f"SELECT id FROM '{self.active_playlist}' WHERE playlists_songs = ?",
                    (self.songs_in_active_playlist[song_index + 1],),
                )
                other_id = cursor.fetchone()[0]

                # Swap their positions
                cursor.execute(
                    f"UPDATE '{self.active_playlist}' SET playlists_songs = ? WHERE id = ?",
                    (self.songs_in_active_playlist[song_index + 1], current_id),
                )
                cursor.execute(
                    f"UPDATE '{self.active_playlist}' SET playlists_songs = ? WHERE id = ?",
                    (song_name, other_id),
                )
                self.console.print(
                    f"[green]Moved '{song_name}' down in playlist[/green]"
                )
                return True
        else:
            self.console.print(
                f"[yellow]Cannot move song {direction} any further[/yellow]"
            )
            return False

    def display_playlist_contents(self, playlist_name=""):
        """Display the contents of a playlist in a formatted table.

        Args:
            playlist_name (str): Name of the playlist to display
        """
        if playlist_name == "":
            self.select_playlist_from_db()
        else:
            self.active_playlist = playlist_name

        self.songs_from_active_playlist()

        table = Table(
            title=f"🎵 Playlist: {self.active_playlist.capitalize()}",
            box=ROUNDED,
            border_style="#D09CFA",
        )
        table.add_column("#", style="dim")
        table.add_column("Song", style="#D7C3F1")

        for i, song in enumerate(self.songs_in_active_playlist, 1):
            table.add_row(str(i), song)

        self.console.print(table)

    def shuffle_playlist(self, playlist_name=""):
        """Get a shuffled version of the playlist songs.

        Args:
            playlist_name (str): Name of the playlist to shuffle

        Returns:
            list: Shuffled song list
        """
        if playlist_name == "":
            self.select_playlist_from_db()
        else:
            self.active_playlist = playlist_name

        self.songs_from_active_playlist()

        shuffled_songs = self.songs_in_active_playlist.copy()
        random.shuffle(shuffled_songs)

        return shuffled_songs
