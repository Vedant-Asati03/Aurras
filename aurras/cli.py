"""
Command Line Interface

This module provides the command-line interface for the Aurras music player.
"""

import sys
import argparse
from pathlib import Path
import logging
import time

from .utils.decorators import handle_exceptions
from .ui.input_handler import HandleUserInput
from .core.downloader import SongDownloader
from .player.online import ListenSongOnline
from .playlist.download import DownloadPlaylist
from .playlist.manager import Select
from .player.history import RecentlyPlayedManager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("aurras.cli")


class AurrasApp:
    """
    Main Aurras application class for the command-line interface.

    This class handles the main application loop and user input.
    """

    def __init__(self):
        """Initialize the AurrasApp class."""
        self.handle_input = HandleUserInput()

    @handle_exceptions
    def run(self):
        """Run the Aurras application."""
        print("Welcome to Aurras Music Player!")
        print(
            "Type '?' followed by a feature name for help, 'help' for full instructions, or start typing to search for a song."
        )

        try:
            while True:
                self.handle_input.handle_user_input()
        except KeyboardInterrupt:
            print("\nThanks for using Aurras!")
            sys.exit(0)


def display_help():
    """Display help information about Aurras music player."""
    print("""
╭───────────────────────────────────────────────────╮
│              AURRAS MUSIC PLAYER HELP             │
╰───────────────────────────────────────────────────╯

USAGE:
  aurras                      - Start the interactive mode
  aurras "song_name"          - Play a song directly
  aurras "song1, song2, ..."  - Queue multiple songs (use commas to separate)
  aurras -d, --download SONG  - Download a song
  aurras -p, --playlist NAME  - Play a playlist
  aurras -dp NAME             - Download a playlist
  aurras -h, --help           - Show this help message
  aurras -v, --version        - Show version information

COMMAND SHORTCUTS (Interactive Mode):
  • d, song1, song2, ...   - Download multiple songs
  • dp, playlist_name      - Download a specific playlist
  • pn, playlist_name      - Play a saved playlist online
  • pf, playlist_name      - Play a downloaded playlist offline
  • rs, playlist_name      - Remove a saved playlist
  • rd, playlist_name      - Remove a downloaded playlist

MAIN COMMANDS (Interactive Mode):
  • help                   - Display this help information
  • queue                  - Display current song queue
  • clear_queue            - Clear the current queue
  • play_offline           - Browse and play downloaded songs
  • download_song          - Download song(s) for offline listening
  • play_playlist          - Play songs from a playlist
  • delete_playlist        - Delete a playlist
  • import_playlist        - Import playlists from Spotify

PLAYBACK CONTROLS:
  • q                      - End current song playback
  • p                      - Pause/Resume playback
  • t                      - Translate lyrics
  • UP/DOWN                - Adjust volume
  • Mouse wheel            - Fine tune volume

For more information, visit: https://github.com/vedant-asati03/Aurras
""")


def download_song(song_name):
    """Download a song or multiple songs."""
    # Check if the song_name contains commas, indicating multiple songs
    if "," in song_name:
        songs = [s.strip() for s in song_name.split(",") if s.strip()]
        print(f"Downloading {len(songs)} songs: {songs}")
        downloader = SongDownloader(songs)
        downloader.download_song()
    else:
        print(f"Downloading song: {song_name}")
        downloader = SongDownloader([song_name])
        downloader.download_song()


def play_song_directly(song_name):
    """Play a single song directly, without using the queue system."""
    logger.info(f"Playing song directly: {song_name}")
    player = ListenSongOnline(song_name)
    player.listen_song_online()


def play_song(song_name):
    """Play a song or multiple songs."""
    logger.info(f"Command-line song argument: '{song_name}'")

    # Check if song_name contains commas, indicating multiple songs
    if "," in song_name:
        songs = [s.strip() for s in song_name.split(",") if s.strip()]
        logger.info(f"Playing {len(songs)} songs in sequence: {songs}")

        # Play songs in sequence directly without queue
        for i, song in enumerate(songs):
            print(f"\n[{i + 1}/{len(songs)}] Now playing: {song}")
            try:
                play_song_directly(song)
            except Exception as e:
                logger.error(f"Error playing {song}: {e}")
                print(f"Error playing {song}: {e}")
    else:
        logger.info(f"Playing single song: {song_name}")
        play_song_directly(song_name)


def play_playlist(playlist_name):
    """Play a playlist."""
    # Check if the playlist name has commas (might be multiple playlists)
    if "," in playlist_name:
        playlists = [p.strip() for p in playlist_name.split(",") if p.strip()]
        print(f"Playing {len(playlists)} playlists in sequence:")
        for i, p_name in enumerate(playlists):
            print(f"\n[{i + 1}/{len(playlists)}] Playing playlist: {p_name}")
            select = Select()
            select.active_playlist = p_name
            select.songs_from_active_playlist()
            for song in select.songs_in_active_playlist:
                play_song_directly(song)
    else:
        print(f"Playing playlist: {playlist_name}")
        select = Select()
        select.active_playlist = playlist_name
        select.songs_from_active_playlist()
        for song in select.songs_in_active_playlist:
            play_song_directly(song)


def download_playlist(playlist_name):
    """Download a playlist or multiple playlists."""
    # Check if the playlist name has commas
    if "," in playlist_name:
        playlists = [p.strip() for p in playlist_name.split(",") if p.strip()]
        print(f"Downloading {len(playlists)} playlists:")
        for i, p_name in enumerate(playlists):
            print(f"\n[{i + 1}/{len(playlists)}] Downloading playlist: {p_name}")
            dl = DownloadPlaylist()
            dl.download_playlist(p_name)
    else:
        print(f"Downloading playlist: {playlist_name}")
        dl = DownloadPlaylist()
        dl.download_playlist(playlist_name)


def display_history(limit=20):
    """Display recently played songs."""
    history_manager = RecentlyPlayedManager()
    history_manager.display_history()


def play_previous_song():
    """Play the previous song from history."""
    history_manager = RecentlyPlayedManager()
    prev_song = history_manager.get_previous_song()

    if prev_song:
        print(f"Playing previous song: {prev_song}")
        play_song_directly(prev_song)
    else:
        print("No previous songs in history.")


def main():
    """Main entry point for the Aurras application."""
    logger.info("Starting Aurras CLI")

    try:
        # Set up argument parser for command-line arguments
        parser = argparse.ArgumentParser(
            description="Aurras - A high-end command line music player",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        parser.add_argument("-v", "--version", action="version", version="Aurras 0.1.0")
        parser.add_argument("-d", "--download", metavar="SONG", help="Download a song")
        parser.add_argument("-p", "--playlist", metavar="NAME", help="Play a playlist")
        parser.add_argument(
            "-dp", "--download-playlist", metavar="NAME", help="Download a playlist"
        )
        # Add new arguments for history functionality
        parser.add_argument(
            "--history", action="store_true", help="Show recently played songs"
        )
        parser.add_argument(
            "--previous",
            action="store_true",
            help="Play the previous song from history",
        )
        parser.add_argument("song", nargs="?", help="Play a song directly")

        # Parse arguments
        args = parser.parse_args()
        logger.debug(f"Parsed arguments: {args}")

        # Handle different command-line arguments
        if args.history:
            display_history()
        elif args.previous:
            play_previous_song()
        elif args.download:
            download_song(args.download)
        elif args.playlist:
            play_playlist(args.playlist)
        elif args.download_playlist:
            download_playlist(args.download_playlist)
        elif args.song:
            play_song(args.song)
        else:
            # Default behavior: run the interactive app
            app = AurrasApp()
            app.run()

    except Exception as e:
        logger.exception("Unhandled exception in main")
        print(f"An error occurred: {e}")
        return 1

    logger.info("Aurras CLI completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
