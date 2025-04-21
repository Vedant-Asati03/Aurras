"""
CLI Dispatcher for Aurras Music Player.

This module provides the main dispatcher for CLI commands,
directing command line arguments to the appropriate command processors.
"""

import sys
import logging
import argparse
import textwrap
from typing import List, Dict, Tuple

from rich.panel import Panel

from ..console import get_console
from ..decorators import handle_exceptions
from ..initialization import initialize_application
from ...ui.core.input_processor import input_processor

from .processors.theme import processor as theme_processor
from .processors.player import processor as player_processor
from .processors.backup import processor as backup_processor
from .processors.history import processor as history_processor
from .processors.library import processor as library_processor
from .processors.playlist import processor as playlist_processor
from .processors.settings import processor as settings_processor

logger = logging.getLogger(__name__)
console = get_console()

# List of available bitrates for song downloads
bitrates = [
    "auto",
    "disable",
    "8k",
    "16k",
    "24k",
    "32k",
    "40k",
    "48k",
    "64k",
    "80k",
    "96k",
    "112k",
    "128k",
    "160k",
    "192k",
    "224k",
    "256k",
    "320k",
    "0",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
]


class SmartFormatter(argparse.HelpFormatter):
    """
    Custom formatter for argparse help text that respects newlines.

    When a help text starts with "N|", the text following it will keep
    its original line breaks.
    """

    def _split_lines(self, text: str, width: int) -> List[str]:
        """Split the text in multiple lines if a line starts with N|"""
        if text.startswith("N|"):
            return text[2:].splitlines()

        text = self._whitespace_matcher.sub(" ", text).strip()
        return textwrap.wrap(text, width)


class AurrasApp:
    """
    Main Aurras application class for the command-line interface.

    This class handles the main application loop and user input.
    """

    def __init__(self):
        """Initialize the AurrasApp class."""

    @handle_exceptions
    def run(self):
        """Run the Aurras application in interactive mode."""
        try:
            while True:
                input_processor.process_input()

        except KeyboardInterrupt:
            console.print("\n[bold green]Thanks for using Aurras![/bold green]")
            sys.exit(0)


def process_command_line_args(argv: List[str]) -> List[str]:
    """
    Process command line arguments to properly handle comma-separated values with spaces.

    This function is more robust in handling complex command lines with quoted arguments.

    Args:
        argv: The raw sys.argv list

    Returns:
        list: Processed argument list
    """
    if len(argv) <= 1:
        return argv

    # Handle the case where the first argument might be a song name without any flags
    if len(argv) == 2 and not argv[1].startswith("-"):
        return argv

    # Parse more complex command lines
    result = [argv[0]]  # Always keep the program name
    i = 1

    while i < len(argv):
        arg = argv[i]
        i += 1

        # Add the argument to our result
        result.append(arg)

        # If this is an option that takes a value
        if arg.startswith("-") and i < len(argv) and not argv[i].startswith("-"):
            # The next arg is the value - look for commas to handle lists
            value_parts = []

            # Keep adding parts until we hit another option or end of args
            while i < len(argv) and not argv[i].startswith("-"):
                value_parts.append(argv[i])
                i += 1

                # If this part doesn't end with a comma, we're done with this value
                if not value_parts[-1].endswith(","):
                    break

            # Add the combined value
            result.append(" ".join(value_parts))

    return result


def create_parser() -> Tuple[
    argparse.ArgumentParser, Dict[str, argparse.ArgumentParser]
]:
    """
    Create and configure the argument parser with subcommands.

    Returns:
        tuple: The configured argument parser and a dictionary of subparsers
    """
    # Initialize argument parser with improved formatter
    parser = argparse.ArgumentParser(
        description="Aurras - A high-end command line music player",
        formatter_class=SmartFormatter,
        epilog="For more information, visit: https://github.com/vedant-asati03/Aurras",
    )

    # Add version argument at the top level
    parser.add_argument("-v", "--version", action="version", version="Aurras 1.1.1")
    parser.add_argument(
        "--help-all", action="store_true", help="Show complete help for all commands"
    )

    # Create subparsers for main commands - use dest="subcommand" to avoid conflict
    subparsers = parser.add_subparsers(dest="subcommand", help="Commands")

    # Create a dictionary to store subparsers for later access
    subparsers_dict = {}

    # Play command - default when no subcommand is given
    subparsers_dict["play"] = subparsers.add_parser(
        "play",
        help="Play a song or playlist",
        description="Play a song, multiple songs, or a playlist",
        formatter_class=SmartFormatter,
    )
    subparsers_dict["play"].add_argument("song", nargs="?", help="Song name to play")
    subparsers_dict["play"].add_argument(
        "--no-lyrics",
        action="store_true",
        help="Disable lyrics display during playback",
    )
    subparsers_dict["play"].add_argument(
        "--shuffle", action="store_true", help="Play songs in random order"
    )
    subparsers_dict["play"].add_argument(
        "--repeat", action="store_true", help="Repeat playback"
    )

    # Download command
    subparsers_dict["download"] = subparsers.add_parser(
        "download",
        help="Download songs or playlists",
        description="Download songs or playlists for offline listening",
        formatter_class=SmartFormatter,
    )
    subparsers_dict["download"].add_argument(
        "song", help="Song name or comma-separated list of songs to download"
    )
    subparsers_dict["download"].add_argument(
        "--playlist",
        metavar="PLAYLIST",
        help="N|Download the specified song[s] as a playlist, if playlist already exists it will be updated\nImportant: This takes priority over the --output-dir argument.",
    )
    subparsers_dict["download"].add_argument(
        "--output-dir",
        metavar="DIR",
        help="N|Specify output directory for downloading songs.\nThis does not change the default output dir, to change that update the settings.",
    )
    subparsers_dict["download"].add_argument(
        "--format",
        choices=["mp3", "flac", "ogg", "opus", "m4a", "wav"],
        help="Set a format for downloading the songs.",
    )
    subparsers_dict["download"].add_argument(
        "--bitrate", choices=bitrates, help="Set audio quality for download."
    )

    # Playlist command
    subparsers_dict["playlist"] = subparsers.add_parser(
        "playlist",
        help="Play or manage playlists",
        description="Play, download, or manage playlists",
        formatter_class=SmartFormatter,
    )
    subparsers_dict["playlist"].add_argument(
        "name", nargs="?", help="Playlist name to play or manage"
    )
    subparsers_dict["playlist"].add_argument(
        "--download",
        action="store_true",
        help="Download the playlist instead of playing it",
    )
    subparsers_dict["playlist"].add_argument(
        "--delete",
        action="store_true",
        help="Delete the specified playlist",
    )
    subparsers_dict["playlist"].add_argument(
        "--import",
        action="store_true",
        help="Import your playlist from Spotify.",
    )
    subparsers_dict["playlist"].add_argument(
        "--search",
        action="store_true",
        help="Find all playlists containing the specified song names or artist name.",
    )
    subparsers_dict["playlist"].add_argument(
        "--list", action="store_true", help="List all available playlists"
    )
    subparsers_dict["playlist"].add_argument(
        "--format",
        choices=["mp3", "flac", "ogg", "opus", "m4a", "wav"],
        help="Set a format for downloading the songs in the playlist",
    )
    subparsers_dict["playlist"].add_argument(
        "--bitrate", choices=bitrates, help="Set audio quality for download."
    )
    subparsers_dict["playlist"].add_argument(
        "--shuffle", action="store_true", help="Shuffle the playlist before playing"
    )
    subparsers_dict["playlist"].add_argument(
        "--no-lyrics",
        action="store_true",
        help="Disable lyrics display during playlist playback",
    )

    # History command
    subparsers_dict["history"] = subparsers.add_parser(
        "history",
        help="View and manage play history",
        description="View, clear, or navigate through your listening history",
        formatter_class=SmartFormatter,
    )
    subparsers_dict["history"].add_argument(
        "--limit",
        type=int,
        default=30,
        help="Limit the number of history entries shown",
    )
    subparsers_dict["history"].add_argument(
        "--clear", action="store_true", help="Clear listening history"
    )
    subparsers_dict["history"].add_argument(
        "--previous", action="store_true", help="Play the previous song from history"
    )

    # Settings command
    subparsers_dict["settings"] = subparsers.add_parser(
        "settings",
        help="View and manage settings",
        description="View and modify application settings",
        formatter_class=SmartFormatter,
    )
    subparsers_dict["settings"].add_argument(
        "--list", action="store_true", help="List all settings and their current values"
    )
    subparsers_dict["settings"].add_argument(
        "--reset", action="store_true", help="Reset all settings to default values"
    )
    subparsers_dict["settings"].add_argument(
        "--set", nargs=2, metavar=("KEY", "VALUE"), help="Set a specific setting value"
    )

    # Theme command
    subparsers_dict["theme"] = subparsers.add_parser(
        "theme",
        help="Manage UI themes",
        description="Apply or list available themes for the application",
        formatter_class=SmartFormatter,
    )
    subparsers_dict["theme"].add_argument("name", nargs="?", help="Theme name to apply")
    subparsers_dict["theme"].add_argument(
        "--list", action="store_true", help="List all available themes"
    )

    # Backup command
    subparsers_dict["backup"] = subparsers.add_parser(
        "backup",
        help="Manage backups",
        description="Create, list, or restore from backups",
        formatter_class=SmartFormatter,
    )
    subparsers_dict["backup"].add_argument(
        "--create", action="store_true", help="Create a new backup"
    )
    subparsers_dict["backup"].add_argument(
        "--list", action="store_true", help="List all available backups"
    )
    subparsers_dict["backup"].add_argument(
        "--restore", metavar="ID", help="Restore from a backup (ID number)"
    )

    # Library command
    subparsers_dict["library"] = subparsers.add_parser(
        "library",
        help="Manage music library",
        description="Scan for new music, manage the library path, and view content",
        formatter_class=SmartFormatter,
    )
    subparsers_dict["library"].add_argument(
        "--scan", action="store_true", help="Scan for new music files"
    )
    subparsers_dict["library"].add_argument(
        "--list-playlists", action="store_true", help="List all saved playlists"
    )
    subparsers_dict["library"].add_argument(
        "--set-path", metavar="PATH", help="Set the library path"
    )
    subparsers_dict["library"].add_argument(
        "--count", action="store_true", help="Show count of songs in library"
    )

    return parser, subparsers_dict


def main():
    """Main entry point for the Aurras application."""
    logger.info("Starting Aurras CLI")
    try:
        initialize_application()

        # If no arguments were provided, start interactive mode
        if len(sys.argv) == 1:
            app = AurrasApp()
            app.run()
            return 0

        # Create parser with subcommands
        parser, subparsers_dict = create_parser()

        # Handle special case for direct song playing without a command
        if (
            len(sys.argv) > 1
            and not sys.argv[1].startswith("-")
            and sys.argv[1]
            not in [
                "play",
                "download",
                "playlist",
                "history",
                "settings",
                "theme",
                "backup",
                "library",
            ]
        ):
            # Assume this is a song name for playing
            song_name = sys.argv[1]
            return player_processor.play_song(song_name, True)

        # Parse arguments
        try:
            args = parser.parse_args()
            logger.debug(f"Parsed arguments: {args}")
        except SystemExit as e:
            return e.code

        # Process based on the subcommand
        subcommand = args.subcommand

        match subcommand:
            case "play":
                return player_processor.play_song(
                    args.song, not getattr(args, "no_lyrics", False)
                )

            case "download":
                return player_processor.download_song(
                    args.song,
                    getattr(args, "playlist", None),
                    getattr(args, "output_dir", None),
                    getattr(args, "format", "mp3"),
                    getattr(args, "bitrate", "auto"),
                )

            case "playlist":
                if getattr(args, "download", False):
                    return playlist_processor.download_playlist(
                        args.name,
                        getattr(args, "format", None),
                        getattr(args, "bitrate", None),
                    )
                elif getattr(args, "delete", False):
                    return playlist_processor.delete_playlist(args.name)
                elif getattr(args, "import", False):
                    return playlist_processor.import_playlist(args.name)
                elif getattr(args, "search", False):
                    return playlist_processor.search_playlists(args.name)
                elif getattr(args, "list", False):
                    return playlist_processor.list_playlists()
                else:
                    return playlist_processor.play_playlist(
                        args.name,
                        not getattr(args, "no_lyrics", False),
                        getattr(args, "shuffle", False),
                    )

            case "history":
                if getattr(args, "clear", False):
                    return history_processor.clear_history()
                elif getattr(args, "previous", False):
                    return history_processor.play_previous_song()
                else:
                    return history_processor.display_history(getattr(args, "limit", 30))

            case "settings":
                if getattr(args, "list", False):
                    return settings_processor.list_settings()
                elif getattr(args, "set", None):
                    key, value = args.set
                    return settings_processor.set_setting(key, value)
                elif getattr(args, "reset", False):
                    return settings_processor.reset_settings()
                else:
                    return settings_processor.open_settings_ui()

            case "theme":
                if getattr(args, "list", False):
                    return theme_processor.list_themes()
                elif args.name:
                    return theme_processor.set_theme(args.name)
                else:
                    return theme_processor.list_themes()

            case "backup":
                if getattr(args, "create", False):
                    return backup_processor.create_backup()
                elif getattr(args, "list", False):
                    return backup_processor.list_backups()
                elif getattr(args, "restore", None) is not None:
                    return backup_processor.restore_backup(args.restore)
                else:
                    return backup_processor.list_backups()

            case "library":
                if getattr(args, "scan", False):
                    return library_processor.scan_library()
                elif getattr(args, "list_playlists", False):
                    return library_processor.list_playlists()
                elif getattr(args, "set_path", None):
                    return library_processor.set_library_path(args.set_path)
                elif getattr(args, "count", False):
                    return library_processor.count_library()
                else:
                    return library_processor.scan_library()

        # If we got here with no subcommand, show help
        if not subcommand:
            parser.print_help()
            return 0

    except KeyboardInterrupt:
        console.print("\n[bold green]Thanks for using Aurras![/bold green]")
        return 0
    except Exception as e:
        logger.exception("Unhandled exception in main")
        console.print(
            Panel(
                f"[bold red]An error occurred:[/bold red] {str(e)}",
                title="[bold red]Error[/bold red]",
                border_style="red",
                padding=(1, 2),
            )
        )
        return 1

    logger.info("Aurras CLI completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
