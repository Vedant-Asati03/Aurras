"""
CLI Dispatcher for Aurras Music Player.

This module provides the main dispatcher for CLI commands,
directing command line arguments to the appropriate command processors.
"""

import sys
import argparse
import textwrap
from typing import List, Dict, Tuple

from aurras import __version__
from aurras.utils.console import console
from aurras.utils.logger import get_logger
from aurras.utils.decorators import handle_exceptions

logger = get_logger("aurras.command.dispatcher", log_to_console=False)

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
        logger.debug("Initializing AurrasApp for interactive mode")

    @handle_exceptions
    def run(self):
        """Run the Aurras application in interactive mode."""
        from aurras.ui.core import input_processor

        logger.info("Starting Aurras interactive mode")

        try:
            while True:
                input_processor.process_input()

        except KeyboardInterrupt:
            logger.info("User exited interactive mode with keyboard interrupt")
            console.print_success("Thanks for using Aurras!")
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
    logger.debug(f"Processing raw command line args: {argv}")

    if len(argv) <= 1:
        logger.debug("No arguments to process")
        return argv

    # Handle the case where the first argument might be a song name without any flags
    if len(argv) == 2 and not argv[1].startswith("-"):
        logger.debug(f"Single non-flag argument detected: {argv[1]}")
        return argv

    # Parse more complex command lines
    result = [argv[0]]  # Always keep the program name
    i = 1

    while i < len(argv):
        arg = argv[i]
        i += 1

        # Add the argument to our result
        result.append(arg)
        logger.debug(f"Added argument: {arg}")

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
            combined_value = " ".join(value_parts)
            result.append(combined_value)
            logger.debug(f"Added option value: {combined_value} for option {arg}")

    logger.debug(f"Processed command line args: {result}")
    return result


def create_parser() -> Tuple[
    argparse.ArgumentParser, Dict[str, argparse.ArgumentParser]
]:
    """
    Create and configure the argument parser with subcommands.

    Returns:
        tuple: The configured argument parser and a dictionary of subparsers
    """
    logger.debug("Creating argument parser with subcommands")

    # Initialize argument parser with improved formatter
    parser = argparse.ArgumentParser(
        description="Aurras - Terminal music elevated!",
        formatter_class=SmartFormatter,
        epilog="For more information, visit: https://github.com/vedant-asati03/Aurras",
    )

    # Add version argument at the top level
    parser.add_argument("-v", "--version", action="version", version=f"Aurras {__version__}",)

    # Create subparsers for main commands - use dest="subcommand" to avoid conflict
    subparsers = parser.add_subparsers(dest="subcommand", help="Commands")
    logger.debug("Created subparsers for main commands")

    # Create a dictionary to store subparsers for later access
    subparsers_dict = {}

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
        help="Download your playlist[s] for offline listening",
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

    # Setup command
    subparsers_dict["setup"] = subparsers.add_parser(
        "setup",
        help="Set up integrations and services",
        description="Configure and manage various service integrations",
        formatter_class=SmartFormatter,
    )
    subparsers_dict["setup"].add_argument(
        "--spotify", action="store_true", help="Set up Spotify integration"
    )
    subparsers_dict["setup"].add_argument(
        "--status", action="store_true", help="Check integration status"
    )
    subparsers_dict["setup"].add_argument(
        "--reset", action="store_true", help="Reset service credentials"
    )

    # Backup command
    subparsers_dict["backup"] = subparsers.add_parser(
        "backup",
        help="Manage backups",
        description="Create, list, or restore from backups",
        formatter_class=SmartFormatter,
    )
    subparsers_dict["backup"].add_argument(
        "--create",
        action="store_true",
        help="Create a new backup of user data",
    )
    subparsers_dict["backup"].add_argument(
        "--list", action="store_true", help="List all available backups"
    )
    subparsers_dict["backup"].add_argument(
        "--delete",
        metavar="ID",
        help="Delete a specific backup by ID",
    )
    subparsers_dict["backup"].add_argument(
        "--restore",
        metavar="ID",
        help="Restore from a specific backup by ID",
    )

    # Self command
    subparsers_dict["self"] = subparsers.add_parser(
        "self",
        help="Manage Aurras installation",
        description="Update, uninstall, or get information about Aurras",
        formatter_class=SmartFormatter,
    )
    # subparsers_dict["self"].add_argument(
    #     "--update",
    #     action="store_true",
    #     help="Update Aurras to the latest version",
    # )
    subparsers_dict["self"].add_argument(
        "--info",
        action="store_true",
        help="Show detailed version and installation information",
    )
    subparsers_dict["self"].add_argument(
        "--uninstall",
        action="store_true",
        help="Uninstall Aurras from the system",
    )
    subparsers_dict["self"].add_argument(
        "--check",
        action="store_true",
        help="Check if all required dependencies are installed",
    )

    logger.debug("Finished configuring all subparsers")
    return parser, subparsers_dict


def main():
    """Main entry point for the Aurras application."""
    logger.info("Starting Aurras CLI")
    try:
        logger.debug(f"Raw command line arguments: {sys.argv}")

        # If no arguments were provided, start interactive mode
        if len(sys.argv) == 1:
            logger.info("No arguments provided, starting interactive mode")
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
                "download",
                "playlist",
                "history",
                "settings",
                "theme",
                "setup",
                "backup",
                "self",
            ]
        ):
            # Assume this is a song name for playing
            from aurras.utils.command.processors import player_processor

            song_name = sys.argv[1]
            logger.info(f"Direct song play request detected: {song_name}")
            return player_processor.play_song(song_name, True)

        processed_args = process_command_line_args(sys.argv)
        if processed_args != sys.argv:
            logger.debug(f"Arguments were processed: {processed_args}")
            sys.argv = processed_args

        try:
            args = parser.parse_args()
            logger.debug(f"Parsed arguments: {args}")
        except SystemExit as e:
            logger.info(f"Parser exited with code {e.code}")
            return e.code

        subcommand = args.subcommand
        logger.info(f"Processing subcommand: {subcommand}")

        match subcommand:
            case "download":
                from aurras.utils.command.processors import player_processor

                logger.debug(f"Executing download command for: {args.song}")
                logger.debug(
                    f"Download options - playlist: {getattr(args, 'playlist', None)}, "
                    f"output_dir: {getattr(args, 'output_dir', None)}, "
                    f"format: {getattr(args, 'format', 'mp3')}, "
                    f"bitrate: {getattr(args, 'bitrate', 'auto')}"
                )
                return player_processor.download_song(
                    args.song,
                    getattr(args, "playlist", None),
                    getattr(args, "output_dir", None),
                    getattr(args, "format", "mp3"),
                    getattr(args, "bitrate", "auto"),
                )

            case "playlist":
                from aurras.utils.command.processors import playlist_processor

                logger.debug(f"Executing playlist command with name: {args.name}")

                if getattr(args, "download", False):
                    logger.info(f"Downloading playlist: {args.name}")
                    return playlist_processor.download_playlist(
                        args.name,
                        getattr(args, "format", None),
                        getattr(args, "bitrate", None),
                    )
                elif getattr(args, "delete", False):
                    logger.info(f"Deleting playlist: {args.name}")
                    return playlist_processor.delete_playlist(args.name)
                elif getattr(args, "import", False):
                    logger.info("Importing Spotify playlists")
                    from aurras.utils.command.processors import spotify_processor

                    return spotify_processor.import_user_playlists()
                elif getattr(args, "search", False):
                    logger.info(f"Searching playlists for: {args.name}")
                    return playlist_processor.search_playlists(args.name)
                elif getattr(args, "list", False):
                    logger.info("Listing all playlists")
                    return playlist_processor.view_playlist(args.name)
                else:
                    logger.info(f"Playing playlist: {args.name}")
                    logger.debug(
                        f"Playlist options - lyrics: {not getattr(args, 'no_lyrics', False)}, "
                        f"shuffle: {getattr(args, 'shuffle', False)}"
                    )
                    return playlist_processor.play_playlist(
                        args.name,
                        not getattr(args, "no_lyrics", False),
                        getattr(args, "shuffle", False),
                    )

            case "history":
                from aurras.utils.command.processors import history_processor

                logger.debug("Executing history command")

                if getattr(args, "clear", False):
                    logger.info("Clearing play history")
                    return history_processor.clear_history()
                elif getattr(args, "previous", False):
                    logger.info("Playing previous song from history")
                    return history_processor.play_previous_song()
                else:
                    logger.info(
                        f"Showing play history with limit: {getattr(args, 'limit', 30)}"
                    )
                    return history_processor.show_history(getattr(args, "limit", 30))

            case "settings":
                from aurras.utils.command.processors import settings_processor

                logger.debug("Executing settings command")

                if getattr(args, "list", False):
                    logger.info("Listing all settings")
                    return settings_processor.list_settings()
                elif getattr(args, "set", None):
                    key, value = args.set
                    logger.info(f"Setting configuration: {key}={value}")
                    return settings_processor.set_setting(key, value)
                elif getattr(args, "reset", False):
                    logger.info("Resetting all settings to defaults")
                    return settings_processor.reset_settings()
                else:
                    logger.info(
                        "No specific settings operation provided, showing settings list"
                    )
                    return settings_processor.list_settings()

            case "theme":
                from aurras.utils.command.processors import theme_processor

                logger.debug("Executing theme command")

                if getattr(args, "list", False):
                    logger.info("Listing all themes")
                    return theme_processor.list_themes()
                elif args.name:
                    logger.info(f"Setting theme to: {args.name}")
                    return theme_processor.set_theme(args.name)
                else:
                    logger.info("No theme name provided, showing theme list")
                    return theme_processor.list_themes()

            case "setup":
                from aurras.utils.command.processors import spotify_processor

                logger.debug("Executing setup command")

                spotify_requested = getattr(args, "spotify", False)
                status_requested = getattr(args, "status", False)
                reset_requested = getattr(args, "reset", False)

                if spotify_requested:
                    if status_requested:
                        logger.info("Checking Spotify integration status")
                        return spotify_processor.check_spotify_status()
                    elif reset_requested:
                        logger.info("Resetting Spotify credentials")
                        return spotify_processor.reset_spotify_credentials()
                    else:
                        logger.info("Setting up Spotify integration")
                        return spotify_processor.setup_spotify()
                elif status_requested or reset_requested:
                    console.print_error(
                        "Please specify a service (e.g., --spotify) with --status or --reset"
                    )
                    return 1
                else:
                    logger.info("No service specified for setup")
                    # Show available setup options
                    console.print_info("Available setup options:")
                    console.print_info(
                        "  --spotify              Set up Spotify integration"
                    )
                    console.print_info(
                        "  --spotify --status     Check Spotify integration status"
                    )
                    console.print_info(
                        "  --spotify --reset      Reset Spotify credentials"
                    )
                    console.print_info("\nExamples:")
                    console.print_info("  aurras setup --spotify")
                    console.print_info("  aurras setup --spotify --status")
                    console.print_info("  aurras setup --spotify --reset")
                    return 1

            case "backup":
                from aurras.utils.command.processors import backup_processor

                logger.debug("Executing backup command")

                if getattr(args, "list", False):
                    logger.info("Listing available backups")
                    return backup_processor.list_backups()
                elif getattr(args, "create", False):
                    logger.info(f"Creating new backup (manual={args.create})")
                    return backup_processor.create_backup(args.create)
                elif getattr(args, "delete", False):
                    logger.info(f"Deleting backup: {args.delete}")
                    return backup_processor.delete_backup(args.delete)
                elif getattr(args, "restore", None) is not None:
                    logger.info(f"Restoring from backup: {args.restore}")
                    return backup_processor.restore_backup(args.restore)
                else:
                    logger.info("No backup operation specified, showing backup list")
                    return backup_processor.list_backups()

            case "self":
                from aurras.utils.command.processors import self_processor

                logger.debug("Executing self command")

                # if getattr(args, "update", False):
                #     logger.info("Updating Aurras to latest version")
                #     return self_processor.update()
                if getattr(args, "uninstall", False):
                    logger.info("Uninstalling Aurras")
                    return self_processor.uninstall()
                elif getattr(args, "info", False):
                    logger.info("Showing version information")
                    return self_processor.get_version_info()
                elif getattr(args, "check", False):
                    logger.info("Checking dependencies")
                    return self_processor.check_dependencies()
                else:
                    logger.info("No self operation specified, showing version info")
                    return self_processor.get_version_info()

        # If we got here with no subcommand, show help
        if not subcommand:
            logger.info("No subcommand specified, showing help")
            parser.print_help()
            return 0

    except KeyboardInterrupt:
        logger.info("User interrupted execution with KeyboardInterrupt")
        console.print_success("Thanks for using Aurras!")
        return 0

    except Exception as e:
        logger.exception(f"Unhandled exception in main: {str(e)}")
        console.print_error(f"An error occurred: {str(e)}")
        return 1

    logger.info("Aurras CLI completed successfully")
    return 0


if __name__ == "__main__":
    exit_code = main()
    logger.debug(f"Exiting with code: {exit_code}")
    sys.exit(exit_code)
