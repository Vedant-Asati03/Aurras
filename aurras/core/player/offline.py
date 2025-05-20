"""
Offline Player Module

This module provides functionality for playing songs from local files.
"""

from typing import List, Tuple

from aurras.utils.console import console
from aurras.utils.logger import get_logger
from aurras.core.downloader import DownloadsDatabase
from aurras.utils.exceptions import (
    AurrasError,
    PlaybackError,
    DatabaseError,
    SongsNotFoundError,
    # PlayerError,
    # MPVLibraryError,
)

from aurras.core.player.mpv import MPVPlayer
from aurras.core.player.mpv.state import PlaybackState
from aurras.core.player.mpv.history_integration import integrate_history_with_playback

logger = get_logger("aurras.core.player.offline", log_to_console=False)


class InitializeOfflinePlayer:
    """
    A class to initialize the offline player components.
    """

    def __init__(self):
        """
        Initialize the offline player components.
        """
        self.player = None
        self.downloads_db = DownloadsDatabase()


class GenerateQueue(InitializeOfflinePlayer):
    """"""

    def __init__(self):
        super().__init__()

    def _songs_fetched_from_db(self):
        """
        Fetch songs from the database.
        """
        try:
            song_dict = self.downloads_db.get_downloaded_songs()
            logger.debug(f"Retrieved {len(song_dict)} songs from the database")
            return song_dict
        except Exception as e:
            logger.error(f"Database error when fetching songs: {e}", exc_info=True)
            raise DatabaseError(f"Failed to fetch songs from database: {e}")

    def create_queues(self) -> Tuple[List[str], List[str]]:
        """
        Create a queue of songs to play.

        Args:
            metadata: Metadata of the song to play
        """
        try:
            metadata = self._songs_fetched_from_db()
            if not metadata:
                logger.warning(
                    "No songs found in the database. Maybe try downloading some first?"
                )
                return [], []

            song_names: List[str] = []
            queue: List[str] = []

            for song_info in metadata:
                # Extract the song name and URL from the metadata
                song_name = song_info.get("track_name")
                song_url = song_info.get("url")

                song_names.append(song_name)
                queue.append(song_url)

                logger.debug(f"Added song to queue: {song_name} - {song_url}")

            return (song_names, queue)
        except DatabaseError:
            # Re-raise database errors
            raise
        except Exception as e:
            logger.error(f"Error creating queue: {e}", exc_info=True)
            raise AurrasError(f"Error preparing song queue: {e}")


class LocalPlaybackHandler(InitializeOfflinePlayer):
    """
    Class to handle local playback of songs and playlists.

    """

    def __init__(self):
        """
        Initialize the offline player.

        Args:
            song_input: Optional specific song to play (bypasses selection)
            playlist_name: Optional playlist name to play from
        """
        super().__init__()
        self.queue = GenerateQueue()

    def add_player(self, player):
        """
        Initialize the MPV player instance.
        """
        self.player = player
        logger.debug("Player instance added to LocalPlaybackHandler")

    def listen_song_offline(
        self, show_lyrics=True, shuffle=False, include_history=False
    ):
        """
        Play downloaded songs directly from the filesystem.

        Args:
            show_lyrics: Whether to show lyrics during playback
            shuffle: Whether to shuffle playback (only applies to playlists)
        """
        try:
            # Fetch songs from the database
            song_names, song_urls = self.queue.create_queues()

            if not song_names:
                console.print_warning(
                    "No songs found in the database. Maybe try downloading some?"
                )
                raise SongsNotFoundError("No songs found in the database")

            # Play songs with or without history integration
            if not include_history:
                self._play_without_history(show_lyrics, shuffle)
            else:
                self._play_with_history(show_lyrics, shuffle)

            logger.debug("Playback completed successfully")

        except KeyboardInterrupt:
            console.print_info("Playback cancelled by user")
            logger.info("Playback cancelled by user")
        # except SongsNotFoundError as e:
        # console.print_error(f"Error: {str(e)}")
        # logger.error(f"Error during offline playback: {e}", exc_info=True)
        # except DatabaseError as e:
        # console.print_error(f"Database error: {str(e)}")
        # logger.error(f"Database error during offline playback: {e}", exc_info=True)
        # except MPVLibraryError as e:
        # console.print(f"[bold red]MPV library error: {str(e)}[/bold red]")
        # logger.error(f"MPV library error: {e}", exc_info=True)
        # except PlayerError as e:
        # console.print(f"[bold red]Player error: {str(e)}[/bold red]")
        # logger.error(f"Player error during offline playback: {e}", exc_info=True)
        # except PlaybackError as e:
        # console.print(f"[bold red]Playback error: {str(e)}[/bold red]")
        # logger.error(f"Offline playback error: {e}", exc_info=True)
        # except AurrasError as e:
        # console.print(f"[bold red]Error: {str(e)}[/bold red]")
        # logger.error(f"Aurras error during offline playback: {e}", exc_info=True)
        except Exception as e:
            console.print_error(f"Unexpected error during offline playback: {str(e)}")
            logger.error(f"Unexpected offline playback error: {e}", exc_info=True)
        finally:
            self._cleanup_player()

    def _play_without_history(self, show_lyrics=True, shuffle=False):
        """Play songs without including history."""
        song_names, song_urls = self.queue.create_queues()
        logger.info(f"Standard playback without history: {len(song_names)} songs")

        try:
            mpv = MPVPlayer(loglevel="error")
            self.add_player(mpv)

            mpv.player(song_urls, song_names, show_lyrics=show_lyrics)
            logger.debug("Song played successfully")
        except Exception as e:
            logger.error(f"Error in offline playback without history: {e}")
            raise PlaybackError(f"Error during offline playback: {e}")

    def _play_with_history(self, show_lyrics=True, shuffle=False):
        """Play songs with history integration."""
        try:
            song_names, song_urls = self.queue.create_queues()
            logger.info(f"Playback with history: {len(song_names)} songs")

            all_songs, all_urls, start_index = integrate_history_with_playback(
                song_names, song_urls
            )

            mpv = MPVPlayer(loglevel="error")
            self.add_player(mpv)

            mpv.player(all_urls, all_songs, show_lyrics, start_index)
            logger.debug("Song played successfully")
        except Exception as e:
            logger.error(f"Error in offline playback with history: {e}")
            raise PlaybackError(f"Error during offline playback with history: {e}")

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
