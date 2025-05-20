"""
Online Player Module

This module provides functionality for playing songs online by streaming.
"""

from typing import List, Union
from rich.progress import SpinnerColumn, TextColumn, Progress

from aurras.utils.logger import get_logger
from aurras.core.player.mpv.core import MPVPlayer
from aurras.core.player.mpv.state import PlaybackState
from aurras.core.player.mpv.history_integration import integrate_history_with_playback
from aurras.services.youtube.search import SearchSong
from aurras.utils.console import console
from aurras.utils.exceptions import (
    # AurrasError,
    # PlaybackError,
    StreamingError,
    # PlaylistNotFoundError,
    SongsNotFoundError,
    # DatabaseError,
    NetworkError,
    # PlayerError,
)

logger = get_logger("aurras.core.player.online", log_to_console=False)


class InitializeOnlinePlayer:
    """Base class for playing songs online."""

    def __init__(self):
        """Initialize the SongPlayer class."""
        self.player = None  # Store the player instance


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
                SpinnerColumn(style=console.primary),
                TextColumn(
                    f"[bold {console.accent}]Searching...[/bold {console.accent}]"
                ),
                transient=True,
            ) as progress:
                task = progress.add_task(
                    f"[{console.text}]{', '.join(_song_name.capitalize() for _song_name in self.search_queries)}[/{console.text}]"
                )
                self.search.search_song()
                progress.update(task, advance=1)
        except Exception as e:
            logger.error(f"Error during song search: {e}")
            raise NetworkError(f"Failed to search for song: {e}")

    def listen_song_online(self, show_lyrics=True, shuffle=False):
        """
        Play the song(s) online by streaming.

        Args:
            show_lyrics: Whether to show lyrics during playback
            playlist_name: Optional name of playlist these songs belong to
            shuffle: Whether to shuffle the playback order
        """
        try:
            self._get_song_info()

            if not self.search.song_name_searched:
                msg = f"No songs found matching: {', '.join(self.search_queries)}"
                logger.warning(msg)
                raise SongsNotFoundError(msg)

            if (
                not hasattr(self.search, "include_history")
                or not self.search.include_history
            ):
                self._play_without_history(show_lyrics)
                return

            self._play_with_history(show_lyrics)

        except KeyboardInterrupt:
            console.print_warning("Playback interrupted by user")
            logger.info("Playback interrupted by user")
        # except SongsNotFoundError as e:
        #     console.print(f"[{error_color}]Error: {str(e)}. No songs found.[/]")
        #     logger.error(f"Playback error: {e}")
        # except PlaylistNotFoundError as e:
        #     console.print(f"[{error_color}]Error: {str(e)}. Playlist not found.[/]")
        #     logger.error(f"Playback error: {e}")
        # except DatabaseError as e:
        #     console.print(f"[{error_color}]Error: {str(e)}. Database error.[/]")
        #     logger.error(f"Playback error: {e}")
        # except NetworkError as e:
        #     console.print(f"[{error_color}]Error: {str(e)}. Network error.[/]")
        #     logger.error(f"Playback error: {e}")
        # except StreamingError as e:
        #     console.print(f"[{error_color}]Error: {str(e)}. Streaming error.[/]")
        #     logger.error(f"Playback error: {e}")
        # except PlayerError as e:
        #     console.print(f"[{error_color}]Error: {str(e)}. Player error.[/]")
        #     logger.error(f"Playback error: {e}")
        # except PlaybackError as e:
        #     console.print(f"[{error_color}]Error: {str(e)}. Playback error.[/]")
        #     logger.error(f"Playback error: {e}")
        # except AurrasError as e:
        #     console.print(f"[{error_color}]Error: {str(e)}. Aurras error.[/]")
        #     logger.error(f"Playback error: {e}")
        except Exception as e:
            console.print_error(f"Unexpected error during playback: {str(e)}")
            logger.error(f"Playback error: {e}")
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
