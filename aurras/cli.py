"""
Command Line Interface

This module provides the command-line interface for the Aurras music player.
"""

import sys
import argparse
import logging
import importlib.util
import signal
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.box import ROUNDED

from .utils.decorators import handle_exceptions
from .ui.input_handler import HandleUserInput
from .core.downloader import SongDownloader
from .player.online import ListenSongOnline
from .playlist.download import DownloadPlaylist
from .playlist.manager import Select
from .player.history import RecentlyPlayedManager
from .utils.initialization import initialize_application  # Add this import

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="aurras.log",  # Log to file instead of console for cleaner UI
)
logger = logging.getLogger("aurras.cli")

# Create a global console object
console = Console()


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
        # Show welcome message with style
        welcome_text = Text("Welcome to Aurras Music Player!", style="bold green")
        help_text = Text(
            "Type '?' for feature help, 'help' for full instructions, or start typing to search for a song.",
            style="cyan",
        )
        panel = Panel.fit(
            Text.assemble(welcome_text, "\n\n", help_text),
            border_style="bright_blue",
            padding=(1, 2),
            title="♪♫ Aurras ♫♪",
            subtitle="v1.1.1",
        )
        console.print(panel)

        try:
            while True:
                self.handle_input.handle_user_input()
        except KeyboardInterrupt:
            console.print("\n[bold green]Thanks for using Aurras![/bold green]")
            sys.exit(0)


def display_help():
    """Display help information about Aurras music player."""
    help_table = Table(
        show_header=False,
        box=ROUNDED,
        border_style="bright_blue",
        title="♪♫ AURRAS MUSIC PLAYER HELP ♫♪",
    )

    help_table.add_column("Section", style="bold cyan")
    help_table.add_column("Description", style="green")

    # Usage section
    help_table.add_row("USAGE", "")
    help_table.add_row("  aurras", "Start the interactive mode")
    help_table.add_row('  aurras "song_name"', "Play a song directly")
    help_table.add_row(
        '  aurras "song1, song2, ..."', "Queue multiple songs (use commas)"
    )
    help_table.add_row("  aurras -d, --download SONG", "Download a song")
    help_table.add_row("  aurras -p, --playlist NAME", "Play a playlist")
    help_table.add_row("  aurras -dp NAME", "Download a playlist")
    help_table.add_row("  aurras --history", "Show recently played songs")
    help_table.add_row("  aurras --previous", "Play previous song from history")
    help_table.add_row("  aurras -h, --help", "Show this help message")
    help_table.add_row("  aurras -v, --version", "Show version information")

    # Shortcuts section
    help_table.add_row("", "")
    help_table.add_row("SHORTCUTS", "")
    help_table.add_row("  d, song1, song2, ...", "Download multiple songs")
    help_table.add_row("  dp, playlist_name", "Download a specific playlist")
    help_table.add_row("  pn, playlist_name", "Play a saved playlist online")
    help_table.add_row("  pf, playlist_name", "Play a downloaded playlist offline")
    help_table.add_row("  rs, playlist_name", "Remove a saved playlist")
    help_table.add_row("  rd, playlist_name", "Remove a downloaded playlist")

    # Commands section
    help_table.add_row("", "")
    help_table.add_row("COMMANDS", "")
    help_table.add_row("  help", "Display this help information")
    help_table.add_row("  queue", "Display current song queue")
    help_table.add_row("  clear_queue", "Clear the current queue")
    help_table.add_row("  history", "Show recently played songs")
    help_table.add_row("  play_offline", "Browse and play downloaded songs")
    help_table.add_row("  download_song", "Download song(s) for offline listening")
    help_table.add_row("  play_playlist", "Play songs from a playlist")
    help_table.add_row("  delete_playlist", "Delete a playlist")
    help_table.add_row("  import_playlist", "Import playlists from Spotify")

    # Playback controls section
    help_table.add_row("", "")
    help_table.add_row("PLAYBACK CONTROLS", "")
    help_table.add_row("  q", "End current song playback")
    help_table.add_row("  b", "Play previous song from history")
    help_table.add_row("  n", "Play next song in queue")
    help_table.add_row("  p", "Pause/Resume playback")
    help_table.add_row("  t", "Translate lyrics")
    help_table.add_row("  UP/DOWN", "Adjust volume")
    help_table.add_row("  Mouse wheel", "Fine tune volume")

    console.print(help_table)
    console.print(
        "\nFor more information, visit: [link=https://github.com/vedant-asati03/Aurras]https://github.com/vedant-asati03/Aurras[/link]"
    )


def download_song(song_name):
    """Download a song or multiple songs."""
    # Check if the song_name contains commas, indicating multiple songs
    if "," in song_name:
        songs = [s.strip() for s in song_name.split(",") if s.strip()]
        with console.status(
            f"[bold green]Preparing to download {len(songs)} songs...[/bold green]"
        ):
            console.print(f"[bold]Songs to download:[/bold]")
            for i, song in enumerate(songs, 1):
                console.print(f"  [cyan]{i}.[/cyan] {song}")

        downloader = SongDownloader(songs)
        downloader.download_song()
    else:
        with console.status(
            f"[bold green]Preparing to download: {song_name}[/bold green]"
        ):
            pass
        downloader = SongDownloader([song_name])
        downloader.download_song()


def play_song_directly(song_name, show_lyrics=True):
    """Play a single song directly, without using the queue system."""
    logger.info(f"Playing song directly: {song_name}")

    with console.status(f"[bold green]Searching for: {song_name}[/bold green]"):
        player = ListenSongOnline(song_name)

    player.listen_song_online(show_lyrics=show_lyrics)


def play_song(song_name, show_lyrics=True):
    """Play a song or multiple songs."""
    logger.info(f"Command-line song argument: '{song_name}'")

    # Check if song_name contains commas, indicating multiple songs
    if "," in song_name:
        songs = [s.strip() for s in song_name.split(",") if s.strip()]
        logger.info(f"Playing {len(songs)} songs in sequence: {songs}")

        # Create a table to display the playlist
        table = Table(title="🎵 Song Playlist", box=ROUNDED, border_style="cyan")
        table.add_column("#", style="dim")
        table.add_column("Song", style="green")

        for i, song in enumerate(songs, 1):
            table.add_row(str(i), song)

        console.print(table)

        # Play songs in sequence directly without queue
        for i, song in enumerate(songs):
            console.rule(f"[bold green]Now playing: {song} [{i + 1}/{len(songs)}]")
            try:
                play_song_directly(song, show_lyrics=show_lyrics)
            except Exception as e:
                logger.error(f"Error playing {song}: {e}")
                console.print(f"[bold red]Error playing {song}: {str(e)}[/bold red]")
    else:
        logger.info(f"Playing single song: {song_name}")
        console.rule(f"[bold green]Now playing: {song_name}")
        play_song_directly(song_name, show_lyrics=show_lyrics)


def play_playlist(playlist_name, show_lyrics=True):
    """Play a playlist."""
    # Check if the playlist name has commas (might be multiple playlists)
    if "," in playlist_name:
        playlists = [p.strip() for p in playlist_name.split(",") if p.strip()]
        console.print(
            f"[bold green]Playing {len(playlists)} playlists in sequence:[/bold green]"
        )
        for i, p_name in enumerate(playlists):
            console.rule(
                f"[bold green]Playing playlist: {p_name} [{i + 1}/{len(playlists)}]"
            )
            select = Select()
            select.active_playlist = p_name
            select.songs_from_active_playlist()
            for song in select.songs_in_active_playlist:
                play_song_directly(song, show_lyrics=show_lyrics)
    else:
        console.rule(f"[bold green]Playing playlist: {playlist_name}")
        select = Select()
        select.active_playlist = playlist_name
        select.songs_from_active_playlist()
        for song in select.songs_in_active_playlist:
            play_song_directly(song, show_lyrics=show_lyrics)


def download_playlist(playlist_name):
    """Download a playlist or multiple playlists."""
    # Check if the playlist name has commas
    if "," in playlist_name:
        playlists = [p.strip() for p in playlist_name.split(",") if p.strip()]
        console.print(
            f"[bold green]Downloading {len(playlists)} playlists:[/bold green]"
        )
        for i, p_name in enumerate(playlists):
            console.rule(
                f"[bold green]Downloading playlist: {p_name} [{i + 1}/{len(playlists)}]"
            )
            dl = DownloadPlaylist()
            dl.download_playlist(p_name)
    else:
        console.rule(f"[bold green]Downloading playlist: {playlist_name}")
        dl = DownloadPlaylist()
        dl.download_playlist(playlist_name)


def display_history(limit=20):
    """Display recently played songs."""
    history_manager = RecentlyPlayedManager()
    history_manager.display_history()


def play_previous_song():
    """Play the previous song from history."""
    history_manager = RecentlyPlayedManager()
    with console.status("[bold green]Finding previous song in history...[/bold green]"):
        prev_song = history_manager.get_previous_song()
    if prev_song:
        console.print(f"[bold green]Playing previous song:[/bold green] {prev_song}")
        play_song_directly(prev_song)
    else:
        console.print("[yellow]No previous songs in history.[/yellow]")


def check_optional_dependencies():
    """Check for optional dependencies and show appropriate messages."""
    missing_features = []

    # Check for lyrics_extractor
    try:
        import lyrics_extractor

        lyrics_available = True
    except ImportError:
        lyrics_available = False
        missing_features.append("lyrics display")

    # Check for googletrans
    try:
        import googletrans

        translation_available = True
    except ImportError:
        translation_available = False
        missing_features.append("lyrics translation")

    # Check for keyboard
    try:
        import keyboard

        keyboard_available = True
    except ImportError:
        keyboard_available = False
        missing_features.append("keyboard shortcuts")

    # Show message if features are missing
    if missing_features and not getattr(
        sys, "frozen", False
    ):  # Don't show in packaged apps
        message = f"[yellow]Some features are limited: {', '.join(missing_features)}.[/yellow]"
        message += "\n[dim]Run 'python setup_dependencies.py --optional' to install optional dependencies.[/dim]"
        console.print(message)

    return True


def main():
    """Main entry point for the Aurras application."""
    logger.info("Starting Aurras CLI")
    try:
        # Initialize the application
        initialize_application()

        # Check optional dependencies at startup
        check_optional_dependencies()

        # Set up argument parser for command-line arguments
        parser = argparse.ArgumentParser(
            description="Aurras - A high-end command line music player",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        parser.add_argument("-v", "--version", action="version", version="Aurras 1.1.1")
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
        # Add no-lyrics option
        parser.add_argument(
            "--no-lyrics",
            action="store_true",
            help="Disable lyrics display during playback",
        )
        parser.add_argument("song", nargs="?", help="Play a song directly")

        # Parse arguments
        args = parser.parse_args()
        logger.debug(f"Parsed arguments: {args}")

        # Show lyrics is true by default, unless --no-lyrics flag is used
        show_lyrics = not args.no_lyrics

        # Handle different command-line arguments
        if args.history:
            display_history()
        elif args.previous:
            play_previous_song()
        elif args.download:
            download_song(args.download)
        elif args.playlist:
            play_playlist(args.playlist, show_lyrics=show_lyrics)
        elif args.download_playlist:
            download_playlist(args.download_playlist)
        elif args.song:
            play_song(args.song, show_lyrics=show_lyrics)
        else:
            # Default behavior: run the interactive app
            app = AurrasApp()
            app.run()
    except Exception as e:
        logger.exception("Unhandled exception in main")
        console.print(f"[bold red]An error occurred:[/bold red] {str(e)}")
        return 1

    logger.info("Aurras CLI completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
