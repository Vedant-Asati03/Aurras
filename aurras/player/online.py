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

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.box import ROUNDED
from rich.style import Style
from rich.text import Text

# Create a global console for consistent styling
console = Console()


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
        self.console = Console()

    def _get_song_info(self):
        """Search for the song and get its metadata."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold green]Searching...[/bold green] {task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task(f"[cyan]{self.search.song_user_searched}[/cyan]")
            self.search.search_song()
            progress.update(task, advance=1)

        text = Text()
        text.append("Found: ", style="bold green")
        text.append(self.search.song_name_searched, style="cyan")
        console.print(text)

    def listen_song_online(self, show_lyrics=True):
        """Play the song online by streaming it."""
        try:
            self._get_song_info()

            mpv_command = self.mpv_command.generate_mpv_command(
                self.search.song_url_searched
            )

            # Create a nice panel for playback info
            song_info = Panel.fit(
                f"[bold cyan]{self.search.song_name_searched}[/bold cyan]",
                title="♪ Now Playing ♪",
                border_style="green",
                padding=(1, 2),
            )
            console.print(song_info)

            # Add to history
            history_manager = RecentlyPlayedManager()

            if not getattr(self, "_navigating_history", False):
                history_manager.add_to_history(self.search.song_name_searched, "online")

            # Play and get the exit code
            exit_code = self.mpv_command.play(
                mpv_command, self.search.song_name_searched, show_lyrics
            )

            # Process exit codes quietly
            if exit_code == 10:  # Previous song (b key)
                prev_song = history_manager.get_previous_song()
                if prev_song and prev_song != self.search.song_name_searched:
                    console.print(
                        f"[bold blue]Playing previous:[/bold blue] {prev_song}"
                    )
                    player = ListenSongOnline(prev_song)
                    player._navigating_history = True
                    player._is_part_of_queue = True
                    player.listen_song_online()
                else:
                    console.print("[yellow]No previous song available[/yellow]")
                return

            elif exit_code == 11:  # Next song (n key)
                next_song = history_manager.get_next_song()
                if next_song:
                    console.print(f"[bold blue]Playing next:[/bold blue] {next_song}")
                    player = ListenSongOnline(next_song)
                    player._navigating_history = True
                    player._is_part_of_queue = True
                    player.listen_song_online()
                    return

            # Normal queue processing
            next_song = self.queue_manager.get_next_song()
            if next_song:
                console.print(f"[bold green]Next in queue:[/bold green] {next_song}")
                next_player = ListenSongOnline(next_song)
                next_player._is_part_of_queue = True
                try:
                    next_player.listen_song_online()
                except Exception as e:
                    console.print(f"[bold red]Error:[/bold red] {str(e)}")
                    another_song = self.queue_manager.get_next_song()
                    if another_song:
                        ListenSongOnline(another_song).listen_song_online()

        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
            if not self._is_part_of_queue:
                next_song = self.queue_manager.get_next_song()
                if next_song:
                    console.print(
                        f"[bold green]Skipping to next song:[/bold green] {next_song}"
                    )
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
        console.print("[yellow]No songs provided to play[/yellow]")
        return

    queue_manager = QueueManager()
    queue_manager.clear_queue()
    queue_manager.add_to_queue(songs)

    # Display nicely formatted queue
    table = Table(title="🎵 Song Queue", box=ROUNDED, border_style="cyan")
    table.add_column("#", style="dim")
    table.add_column("Song", style="green")

    for i, song in enumerate(songs, 1):
        table.add_row(str(i), song)

    console.print(table)

    # Start playing the first song
    first_song = queue_manager.get_next_song()
    if first_song:
        console.rule(f"[bold green]Now playing: {first_song}")
        player = ListenSongOnline(first_song)
        player._is_part_of_queue = True
        player.listen_song_online()


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
