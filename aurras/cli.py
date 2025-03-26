"""
Command Line Interface

This module provides the command-line interface for the Aurras music player.
"""

import sys
import argparse
import logging
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.box import ROUNDED

from .ui.command_handler import InputCases
from .utils.decorators import handle_exceptions
from .ui.input_handler import HandleUserInput
from .playlist.download import DownloadPlaylist
from .player.history import RecentlyPlayedManager
from .utils.initialization import initialize_application

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="aurras.log",
)
logger = logging.getLogger("aurras.cli")

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
    logger.info(f"Command-line download argument: '{song_name}'")

    if song_name and (
        (song_name.startswith('"') and song_name.endswith('"'))
        or (song_name.startswith("'") and song_name.endswith("'"))
    ):
        song_name = song_name[1:-1]

    InputCases().download_song(song_name)


def play_song(song_name, show_lyrics=True):
    """Play a song or multiple songs."""
    logger.info(f"Command-line song argument: '{song_name}'")

    # Strip outer quotes if present
    if song_name and (
        (song_name.startswith('"') and song_name.endswith('"'))
        or (song_name.startswith("'") and song_name.endswith("'"))
    ):
        song_name = song_name[1:-1]

    InputCases().song_searched(song_name, show_lyrics)


def play_playlist(playlist_name, show_lyrics=True):
    """Play a playlist."""
    if playlist_name and (
        (playlist_name.startswith('"') and playlist_name.endswith('"'))
        or (playlist_name.startswith("'") and playlist_name.endswith("'"))
    ):
        playlist_name = playlist_name[1:-1]

    if "," in playlist_name:
        playlists = [p.strip() for p in playlist_name.split(",") if p.strip()]
        console.print(
            f"[bold green]Playing {len(playlists)} playlists in sequence:[/bold green]"
        )
        for i, p_name in enumerate(playlists):
            InputCases().play_playlist(playlist_name=p_name)

    else:
        console.rule(f"[bold green]Playing playlist: {playlist_name}")
        InputCases().play_playlist(playlist_name=playlist_name, show_lyrics=show_lyrics)


def download_playlist(playlist_name):
    """Download a playlist or multiple playlists."""
    if playlist_name and (
        (playlist_name.startswith('"') and playlist_name.endswith('"'))
        or (playlist_name.startswith("'") and playlist_name.endswith("'"))
    ):
        playlist_name = playlist_name[1:-1]

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


def display_history(limit=30):
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
        InputCases().song_searched(prev_song)
    else:
        console.print("[yellow]No previous songs in history.[/yellow]")


def check_optional_dependencies():
    """Check for optional dependencies and show appropriate messages."""
    missing_features = []

    try:
        import lyrics_extractor

        lyrics_available = True
    except ImportError:
        lyrics_available = False
        missing_features.append("lyrics display")

    try:
        import googletrans

        translation_available = True
    except ImportError:
        translation_available = False
        missing_features.append("lyrics translation")

    try:
        import keyboard

        keyboard_available = True
    except ImportError:
        keyboard_available = False
        missing_features.append("keyboard shortcuts")

    if missing_features and not getattr(sys, "frozen", False):
        message = f"[yellow]Some features are limited: {', '.join(missing_features)}.[/yellow]"
        message += "\n[dim]Run 'python setup_dependencies.py --optional' to install optional dependencies.[/dim]"
        console.print(message)

    return True


def process_command_line_args(argv):
    """
    Process command line arguments to properly handle comma-separated values with spaces.

    Args:
        argv: The raw sys.argv list

    Returns:
        list: Processed argument list
    """
    if len(argv) <= 1:
        return argv

    new_argv = [argv[0]]
    i = 1

    while i < len(argv):
        arg = argv[i]

        if arg.startswith("-"):
            new_argv.append(arg)

            # Options that take values
            value_options = [
                "-d",
                "--download",
                "-p",
                "--playlist",
                "-dp",
                "--download-playlist",
            ]

            if arg in value_options and i + 1 < len(argv):
                next_arg = argv[i + 1]

                # If next arg isn't an option, it's the value for this option
                if not next_arg.startswith("-"):
                    # Process potentially comma-separated values
                    combined_value = [next_arg]
                    j = i + 2

                    # Continue collecting parts as long as they're not new options
                    # and there are commas indicating a list
                    while (
                        j < len(argv)
                        and not argv[j].startswith("-")
                        and ("," in next_arg or "," in argv[j - 1])
                    ):
                        combined_value.append(argv[j])
                        j += 1

                    new_argv.append(" ".join(combined_value))
                    i = j - 1  # Skip ahead
                else:
                    # Option followed by another option - first one has no value
                    pass
            i += 1
        else:
            # Handle positional arguments
            if i == len(argv) - 1 or argv[i + 1].startswith("-"):
                # Simple case: last arg or next is an option
                new_argv.append(arg)
            elif "," in arg or (i > 1 and "," in argv[i - 1]):
                # Part of a comma-separated list
                combined_args = [arg]
                j = i + 1

                while j < len(argv) and not argv[j].startswith("-"):
                    combined_args.append(argv[j])
                    j += 1

                new_argv.append(" ".join(combined_args))
                i = j - 1  # Skip the parts we've combined
            else:
                # Standard argument
                new_argv.append(arg)
            i += 1

    return new_argv


def main():
    """Main entry point for the Aurras application."""
    logger.info("Starting Aurras CLI")
    try:
        initialize_application()

        check_optional_dependencies()

        if len(sys.argv) > 1:
            sys.argv = process_command_line_args(sys.argv)

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
        parser.add_argument(
            "--history", action="store_true", help="Show recently played songs"
        )
        parser.add_argument(
            "--shuffle", action="store_true", help="Play songs in random order"
        )
        parser.add_argument("--repeat", action="store_true", help="Repeat playback")
        parser.add_argument(
            "--search", metavar="QUERY", help="Search for songs matching query"
        )
        parser.add_argument(
            "--previous",
            action="store_true",
            help="Play the previous song from history",
        )
        parser.add_argument(
            "--no-lyrics",
            action="store_true",
            help="Disable lyrics display during playback",
        )
        parser.add_argument("song", nargs="?", help="Play a song directly")

        args = parser.parse_args()
        logger.debug(f"Parsed arguments: {args}")

        # Show lyrics is true by default, unless --no-lyrics flag is used
        show_lyrics = not args.no_lyrics

        # Check for shuffle and repeat options
        # play_options = {}
        # if hasattr(args, "shuffle") and args.shuffle:
        #     play_options["shuffle"] = True
        # if hasattr(args, "repeat") and args.repeat:
        #     play_options["repeat"] = True

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
            # Default behavior: run the interactive mode
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
