"""
Command Line Interface

This module provides the command-line interface for the Aurras music player.
"""

import sys
import argparse
from pathlib import Path

from .utils.decorators import handle_exceptions
from .ui.input_handler import HandleUserInput
from .core.downloader import SongDownloader
from .player.online import ListenSongOnline
from .playlist.download import DownloadPlaylist
from .playlist.manager import Select


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
    """Download a song."""
    print(f"Downloading song: {song_name}")
    downloader = SongDownloader([song_name])
    downloader.download_song()


def play_song(song_name):
    """Play a song."""
    print(f"Playing song: {song_name}")
    player = ListenSongOnline(song_name)
    player.listen_song_online()


def play_playlist(playlist_name):
    """Play a playlist."""
    print(f"Playing playlist: {playlist_name}")
    select = Select()
    select.active_playlist = playlist_name
    select.songs_from_active_playlist()
    for song in select.songs_in_active_playlist:
        play_song(song)


def download_playlist(playlist_name):
    """Download a playlist."""
    print(f"Downloading playlist: {playlist_name}")
    dl = DownloadPlaylist()
    dl.download_playlist(playlist_name)


def main():
    """Main entry point for the Aurras application."""
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
    parser.add_argument("song", nargs="?", help="Play a song directly")

    # Parse arguments
    args = parser.parse_args()

    # Handle different command-line arguments
    # Note: Remove the check for args.help since argparse handles --help internally
    if args.download:
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


if __name__ == "__main__":
    main()
