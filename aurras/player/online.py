"""
Online Player Module

This module provides functionality for playing songs online by streaming.
"""

import random
import sqlite3
import logging
from typing import List, Union

from rich.table import Table
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.box import ROUNDED

from ..core.downloader import DownloadsDatabase
from ..services.youtube.search import SearchSong
from ..utils.path_manager import PathManager
from ..utils.exceptions import (
    AurrasError,
    PlaybackError,
    StreamingError,
    PlaylistError,
    PlaylistNotFoundError,
    SongsNotFoundError,
    DatabaseError,
    NetworkError,
    PlayerError,
)

from .mpv.core import MPVPlayer
from .mpv.state import PlaybackState
from ..playlist.manager import Select
from .mpv.history_integration import integrate_history_with_playback

console = Console()
logger = logging.getLogger(__name__)


class InitializeOnlinePlayer:
    """Base class for playing songs online."""

    def __init__(self):
        """Initialize the SongPlayer class."""
        self.player = None  # Store the player instance
        self.downloads_db = DownloadsDatabase()


class SongStreamHandler(InitializeOnlinePlayer):
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
        self.path_manager = PathManager()
        self._is_part_of_queue = False

    def add_player(self, player):
        """
        Store the player instance for later access.

        Args:
            player: The MPVPlayer instance
        """
        self.player = player
        logger.debug("Player instance added to SongStreamHandler")

    def _get_song_info(self):
        """Search for the song(s) and get metadata."""
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold green]Searching...[/bold green] {task.description}"),
                console=console,
                transient=True,
            ) as progress:
                task = progress.add_task(
                    f"[cyan]{', '.join(_song_name.capitalize() for _song_name in self.search_queries)}[/cyan]"
                )
                self.search.search_song()
                progress.update(task, advance=1)
        except Exception as e:
            logger.error(f"Error during song search: {e}")
            raise NetworkError(f"Failed to search for song: {e}")

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
                msg = f"No songs found matching: {', '.join(self.search_queries)}"
                logger.warning(msg)
                raise SongsNotFoundError(msg)

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
        except SongsNotFoundError as e:
            console.print(f"[bold red]{str(e)}[/bold red]")
        except PlaylistNotFoundError as e:
            console.print(f"[bold red]{str(e)}[/bold red]")
        except DatabaseError as e:
            console.print(f"[bold red]Database error: {str(e)}[/bold red]")
            logger.error(f"Database error during playback: {e}", exc_info=True)
        except NetworkError as e:
            console.print(f"[bold red]Network error: {str(e)}[/bold red]")
            logger.error(f"Network error during playback: {e}", exc_info=True)
        except StreamingError as e:
            console.print(f"[bold red]Streaming error: {str(e)}[/bold red]")
            logger.error(f"Streaming error: {e}", exc_info=True)
        except PlayerError as e:
            console.print(f"[bold red]Player error: {str(e)}[/bold red]")
            logger.error(f"Player error: {e}", exc_info=True)
        except PlaybackError as e:
            console.print(f"[bold red]Playback error: {str(e)}[/bold red]")
            logger.error(f"Online Playback error: {e}", exc_info=True)
        except AurrasError as e:
            console.print(f"[bold red]Error: {str(e)}[/bold red]")
            logger.error(f"Aurras error during playback: {e}", exc_info=True)
        except Exception as e:
            console.print(f"[bold red]Unexpected error: {str(e)}[/bold red]")
            logger.error(f"Unexpected error during playback: {e}", exc_info=True)
        finally:
            # Important: ensure player is terminated when done
            self._cleanup_player()

    def _play_without_history(self, show_lyrics=True, shuffle=False):
        """Play songs without including history."""
        logger.info(
            f"Standard playback without history: {len(self.search.song_name_searched)} songs"
        )
        try:
            mpv = MPVPlayer(loglevel="error")
            self.add_player(mpv)

            mpv.player(
                self.search.song_url_searched,
                self.search.song_name_searched,
                show_lyrics,
            )
            logger.debug("Song played successfully")
        except Exception as e:
            logger.error(f"Error in playback without history: {e}")
            raise StreamingError(f"Error during streaming playback: {e}")

    def _play_with_history(self, show_lyrics=True, shuffle=False):
        """Play songs with history integration."""
        try:
            logger.info(
                f"Playing with history integration: {len(self.search.song_name_searched)} searched songs"
            )

            all_songs, all_urls, start_index = integrate_history_with_playback(
                self.search.song_name_searched, self.search.song_url_searched
            )

            mpv = MPVPlayer(loglevel="error")
            self.add_player(mpv)

            mpv.player(all_urls, all_songs, show_lyrics, start_index)
            logger.debug("Song played successfully")
        except Exception as e:
            logger.error(f"Error in playback with history: {e}")
            raise StreamingError(f"Error during streaming playback with history: {e}")

    def _prepare_playlist(self, playlist_name: str, shuffle: bool = False):
        """
        Prepare and play songs from a playlist.

        Args:
            playlist_name: Name of the playlist to play
            shuffle: Whether to shuffle the playlist
        """
        playlist_select = Select()

        try:
            # Verify the playlist exists
            with sqlite3.connect(self.path_manager.saved_playlists) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (playlist_name.lower(),),
                )
                if not cursor.fetchone():
                    raise PlaylistNotFoundError(
                        f"Playlist '{playlist_name}' doesn't exist."
                    )

                # Set the active playlist
                playlist_select.active_playlist = playlist_name.lower()

                # Get all songs from the playlist
                cursor.execute(f"SELECT playlists_songs FROM '{playlist_name.lower()}'")
                playlist_songs = [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"SQLite error with playlist {playlist_name}: {e}")
            raise DatabaseError(
                f"Database error accessing playlist '{playlist_name}': {e}"
            )

        if not playlist_songs:
            raise PlaylistError(f"Playlist '{playlist_name}' is empty.")

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
                song_player = SongStreamHandler(song)
                song_player.listen_song_online(show_lyrics=True)

                # Add to history
                if hasattr(self, "history_manager") and self.history_manager:
                    self.history_manager.add_to_history(
                        song, f"playlist:{playlist_name}"
                    )
            except KeyboardInterrupt:
                console.print("[yellow]Playback stopped by user[/yellow]")
                break
            except PlaybackError as e:
                console.print(f"[bold red]Playback error for '{song}': {e}[/bold red]")
                logger.error(f"Error playing playlist song: {e}", exc_info=True)
                # Continue with next song
                continue
            except Exception as e:
                console.print(f"[bold red]Error playing '{song}': {e}[/bold red]")
                logger.error(f"Error playing playlist song: {e}", exc_info=True)
                # Continue with next song
                continue

    def _cleanup_player(self):
        """Clean up the player instance to avoid resource leaks."""
        if hasattr(self, "player") and self.player:
            try:
                # Mark the player as stopping before cleanup
                if hasattr(self.player, "_state"):
                    self.player._state.stop_requested = True
                    self.player._state.playback_state = PlaybackState.STOPPED

                # If it has terminate method, call it
                if hasattr(self.player, "terminate"):
                    self.player.terminate()
                else:
                    # Just delete the reference
                    del self.player

                self.player = None
            except Exception as e:
                logger.warning(f"Error cleaning up player: {e}")
                # Ensure player is set to None even if cleanup fails
                self.player = None
