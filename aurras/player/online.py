"""
Online Player Module

This module provides functionality for playing songs online by streaming.
"""

import sqlite3
from typing import List, Union
import random
from rich.table import Table
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.box import ROUNDED
import logging

from ..utils.path_manager import PathManager
from ..utils.config import Config
from ..services.youtube.search import SearchSong

from .mpv import MPVPlayer
from ..playlist.manager import Select
from ..player.history import RecentlyPlayedManager

console = Console()
logger = logging.getLogger(__name__)


class OnlineSongPlayer:
    """Base class for playing songs online."""

    def __init__(self):
        """Initialize the SongPlayer class."""
        self.config = Config()
        self.player = None  # Store the player instance


class ListenSongOnline(OnlineSongPlayer):
    """
    A class for listening to songs online with support for single songs,
    multiple songs, and playlists.

    Attributes:
        search: SearchSong instance with search queries
        queue_manager: QueueManager instance for queue management
        history_manager: RecentlyPlayedManager for tracking song history
    """

    def __init__(self, song_input: Union[str, List[str]]):
        """
        Initialize the ListenSongOnline class.

        Args:
            song_input: Either a single song as a string or a list of songs to play
        """
        super().__init__()
        # Normalize input to a list if it's a string
        self.search_queries = (
            [song_input] if isinstance(song_input, str) else song_input
        )
        self.search = SearchSong(self.search_queries)
        self.history_manager = RecentlyPlayedManager()
        self.path_manager = PathManager()
        self._is_part_of_queue = False

    def add_player(self, player):
        """
        Store the player instance for later access.

        Args:
            player: The MPVPlayer instance
        """
        self.player = player
        logger.debug("Player instance added to ListenSongOnline")

    def _get_song_info(self):
        """Search for the song(s) and get metadata."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold green]Searching...[/bold green] {task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task(f"[cyan]{', '.join(self.search_queries)}[/cyan]")
            self.search.search_song()
            progress.update(task, advance=1)

    def listen_song_online(self, show_lyrics=True, playlist_name=None, shuffle=False):
        """
        Play the song(s) online by streaming.

        Args:
            show_lyrics: Whether to show lyrics during playback
            playlist_name: Optional name of playlist these songs belong to
            shuffle: Whether to shuffle the playback order
        """
        try:
            # If we're playing a playlist, extract the songs first
            if playlist_name:
                self._prepare_playlist(playlist_name, shuffle)
                return

            # Regular song search
            self._get_song_info()

            if not self.search.song_name_searched:
                console.print("[bold red]No song found with that name.[/bold red]")
                return

            # Get history songs
            # Default playback (searched songs only)
            if (
                not hasattr(self.search, "include_history")
                or not self.search.include_history
            ):
                self._play_without_history(show_lyrics)
                return

            # Play with history integration
            self._play_with_history(show_lyrics)

        except KeyboardInterrupt:
            console.print("[yellow]Playback stopped by user[/yellow]")
        except Exception as e:
            console.print(f"[bold red]Error during playback: {e}[/bold red]")
            logger.error(f"Playback error: {e}", exc_info=True)
        finally:
            # Important: ensure player is terminated when done
            self._cleanup_player()

    def _play_without_history(self, show_lyrics=True):
        """Play songs without including history."""
        logger.info(
            f"Standard playback without history: {len(self.search.song_name_searched)} songs"
        )
        console.rule("[bold green]Playing Without History")

        # Create and store the player instance
        mpv = MPVPlayer(loglevel="error")
        self.add_player(mpv)

        # Add to history
        if not getattr(self, "_navigating_history", False):
            for song in self.search.song_name_searched:
                self.history_manager.add_to_history(song, "online")

        # Standard playback
        mpv.player(
            self.search.song_url_searched,
            self.search.song_name_searched,
            show_lyrics,
        )
        logger.debug("Song played successfully")

    def _play_with_history(self, show_lyrics=True):
        """Play songs with history integration."""
        # Get recent history
        recent_history = self.history_manager.get_recent_songs(20)

        # IMPORTANT: Reverse the history list so oldest songs play first
        # History comes from DB ordered by most recent first, we need oldest first
        recent_history.reverse()

        history_songs = [song["song_name"] for song in recent_history]

        # SIMPLIFIED APPROACH: Just make a combined list with history first
        all_songs = history_songs + self.search.song_name_searched
        start_index = len(history_songs)  # This is where the searched songs start

        # Find URLs for history songs
        history_urls = []
        for song_name in history_songs:
            # For simplicity, we'll just use the song name as search query
            # This will use YouTube search on demand for each history song
            temp_search = SearchSong([song_name])
            temp_search.search_song(
                include_history=False
            )  # Don't include history to avoid recursion

            if temp_search.song_url_searched:
                history_urls.append(temp_search.song_url_searched[0])
            else:
                # If we can't find a URL, skip this song
                logger.warning(f"Could not find URL for history song: {song_name}")
                continue

        all_urls = history_urls + self.search.song_url_searched

        # Display info
        logger.info(
            f"Playing with history integration: {len(all_songs)} total songs, starting at {start_index}"
        )
        console.rule("[bold green]Queue with History")

        # Display info about history
        if history_songs:
            history_str = ", ".join(history_songs[: min(3, len(history_songs))])
            console.print(
                f"[dim]History songs in queue ({len(history_songs)}): {history_str}...[/dim]"
            )

        # Display info about searched songs
        searched_str = ", ".join(
            self.search.song_name_searched[
                : min(3, len(self.search.song_name_searched))
            ]
        )
        console.print(f"[green]Starting with: {searched_str}...[/green]")

        # Create and store the player instance
        mpv = MPVPlayer(loglevel="error")
        self.add_player(mpv)

        # Add searched songs to history
        if not getattr(self, "_navigating_history", False):
            for song in self.search.song_name_searched:
                self.history_manager.add_to_history(song, "online")

        # Play with history and start index
        mpv.player(all_urls, all_songs, show_lyrics, start_index)

    def _prepare_playlist(self, playlist_name: str, shuffle: bool = False):
        """
        Prepare and play songs from a playlist.

        Args:
            playlist_name: Name of the playlist to play
            shuffle: Whether to shuffle the playlist
        """
        playlist_select = Select()

        # Verify the playlist exists
        with sqlite3.connect(self.path_manager.saved_playlists) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (playlist_name.lower(),),
            )
            if not cursor.fetchone():
                console.print(
                    f"[bold red]Playlist '{playlist_name}' doesn't exist.[/bold red]"
                )
                return

            # Set the active playlist
            playlist_select.active_playlist = playlist_name.lower()

            # Get all songs from the playlist
            cursor.execute(f"SELECT playlists_songs FROM '{playlist_name.lower()}'")
            playlist_songs = [row[0] for row in cursor.fetchall()]

        if not playlist_songs:
            console.print(f"[bold red]Playlist '{playlist_name}' is empty.[/bold red]")
            return

        # Shuffle if requested
        if shuffle:
            random.shuffle(playlist_songs)
            # Create a nice table to show the shuffled playlist
            shuffle_table = Table(
                title="🎲 Shuffled Playlist", box=ROUNDED, border_style="#D09CFA"
            )
            shuffle_table.add_column("#", style="dim")
            shuffle_table.add_column("Song", style="#D7C3F1")

            for i, song in enumerate(playlist_songs, 1):
                shuffle_table.add_row(str(i), song)

            console.print(shuffle_table)
        else:
            # Create a nice table to show the playlist
            playlist_table = Table(
                title=f"🎵 Playlist: {playlist_name}", box=ROUNDED, border_style="cyan"
            )
            playlist_table.add_column("#", style="dim")
            playlist_table.add_column("Song", style="green")

            for i, song in enumerate(playlist_songs, 1):
                playlist_table.add_row(str(i), song)

            console.print(playlist_table)

        # Play each song in the playlist
        for i, song in enumerate(playlist_songs):
            try:
                console.rule(
                    f"[bold green]Playing {i + 1}/{len(playlist_songs)}: {song}"
                )

                # Create a new search for each song
                song_player = ListenSongOnline(song)
                song_player.listen_song_online(show_lyrics=True)

                # Add to history
                self.history_manager.add_to_history(song, f"playlist:{playlist_name}")
            except KeyboardInterrupt:
                console.print("[yellow]Playback stopped by user[/yellow]")
                break
            except Exception as e:
                console.print(f"[bold red]Error playing '{song}': {e}[/bold red]")
                logger.error(f"Error playing playlist song: {e}", exc_info=True)
                # Continue with next song
                continue

    def _cleanup_player(self):
        """Clean up the player instance to avoid resource leaks."""
        if hasattr(self, "player") and self.player:
            try:
                del self.player
            except Exception as e:
                logger.warning(f"Error cleaning up player: {e}")
