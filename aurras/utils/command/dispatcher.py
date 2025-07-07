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

logger = get_logger("aurras.command.dispatcher")

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
        logger.debug(
            "Initializing AurrasApp for interactive mode",
            extra={"mode": "interactive", "component": "aurras_app"},
        )

    @handle_exceptions
    def run(self):
        """Run the Aurras application in interactive mode."""
        from aurras.ui.core import input_processor

        logger.info(
            "Starting Aurras interactive mode",
            extra={"mode": "interactive", "component": "aurras_app"},
        )

        try:
            with logger.operation_context(
                operation="interactive_session", mode="interactive"
            ):
                while True:
                    input_processor.process_input()

        except KeyboardInterrupt:
            logger.info(
                "User exited interactive mode",
                extra={"exit_reason": "keyboard_interrupt", "mode": "interactive"},
            )
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
    logger.debug(
        "Processing command line arguments",
        extra={"args_count": len(argv), "operation": "arg_processing"},
    )

    if len(argv) <= 1:
        return argv

    # Handle the case where the first argument might be a song name without any flags
    if len(argv) == 2 and not argv[1].startswith("-"):
        # Only log direct song play if it's not a valid subcommand
        if argv[1] not in [
            "download",
            "playlist",
            "history",
            "settings",
            "theme",
            "setup",
            "backup",
            "self",
        ]:
            logger.debug(
                "Direct song play detected",
                extra={"song_name": argv[1], "type": "direct_play"},
            )
        return argv

    # Parse more complex command lines
    result = [argv[0]]  # Always keep the program name
    i = 1

    with logger.operation_context(operation="complex_arg_parsing"):
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
                combined_value = " ".join(value_parts)
                result.append(combined_value)
                logger.debug(
                    "Combined option value",
                    extra={"option": arg, "value": combined_value},
                )

    if result != argv:
        logger.debug(
            "Arguments were processed",
            extra={"modified": True, "processed_count": len(result)},
        )
    return result


def create_parser() -> Tuple[
    argparse.ArgumentParser, Dict[str, argparse.ArgumentParser]
]:
    """
    Create and configure the argument parser with subcommands.

    Returns:
        tuple: The configured argument parser and a dictionary of subparsers
    """
    logger.debug("Creating argument parser", extra={"component": "cli_parser"})

    # Initialize argument parser with improved formatter
    parser = argparse.ArgumentParser(
        description="Aurras - Terminal music elevated!",
        formatter_class=SmartFormatter,
        epilog="For more information, visit: https://github.com/vedant-asati03/Aurras",
    )

    # Add version argument at the top level
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"Aurras {__version__}",
    )

    # Add debug flag at the top level
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="run aurras in debug mode with detailed console output",
    )

    # Add suppress flag for debug mode
    parser.add_argument(
        "--suppress",
        choices=["debug", "info", "all"],
        help="suppress specific log levels from console output (requires --debug)",
    )

    # Create subparsers for main commands - use dest="subcommand" to avoid conflict
    subparsers = parser.add_subparsers(dest="subcommand", help="Commands")

    # Create a dictionary to store subparsers for later access
    subparsers_dict = {}

    with logger.operation_context(operation="subcommand_configuration"):
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
            "--previous",
            action="store_true",
            help="Play the previous song from history",
        )

        # Settings command
        subparsers_dict["settings"] = subparsers.add_parser(
            "settings",
            help="View and manage settings",
            description="View and modify application settings",
            formatter_class=SmartFormatter,
        )
        subparsers_dict["settings"].add_argument(
            "--list",
            action="store_true",
            help="List all settings and their current values",
        )
        subparsers_dict["settings"].add_argument(
            "--reset", action="store_true", help="Reset all settings to default values"
        )
        subparsers_dict["settings"].add_argument(
            "--set",
            nargs=2,
            metavar=("KEY", "VALUE"),
            help="Set a specific setting value",
        )

        # Theme command
        subparsers_dict["theme"] = subparsers.add_parser(
            "theme",
            help="Manage UI themes",
            description="Apply or list available themes for the application",
            formatter_class=SmartFormatter,
        )
        subparsers_dict["theme"].add_argument(
            "name", nargs="?", help="Theme name to apply"
        )
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

    logger.debug(
        "Finished configuring subparsers",
        extra={"total_subcommands": len(subparsers_dict)},
    )
    return parser, subparsers_dict


def main():
    """Main entry point for the Aurras application."""
    logger.info("Starting Aurras CLI", extra={"version": __version__})

    try:
        # If no arguments were provided, start interactive mode
        if len(sys.argv) == 1:
            logger.info("No arguments provided, starting interactive mode")
            app = AurrasApp()
            app.run()
            return 0

        # Create parser with subcommands
        with logger.profile_context("parser_creation"):
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
            from aurras.utils.command.processors import processor

            song_name = sys.argv[1]
            logger.info("Direct song play request", extra={"song_name": song_name})
            return processor.player_processor.play_song(song_name, True)

        # Process command line arguments
        processed_args = process_command_line_args(sys.argv)
        if processed_args != sys.argv:
            sys.argv = processed_args

        # Parse arguments
        try:
            args = parser.parse_args()
            logger.debug(
                "Arguments parsed successfully",
                extra={"subcommand": getattr(args, "subcommand", None)},
            )
        except SystemExit as e:
            logger.debug("Parser exited", extra={"exit_code": e.code})
            return e.code

        subcommand = args.subcommand
        logger.info("Processing subcommand", extra={"subcommand": subcommand})

        match subcommand:
            case "download":
                from aurras.utils.command.processors import processor

                with logger.operation_context(
                    operation="download_command", subcommand="download"
                ):
                    logger.debug(
                        "Executing download command",
                        extra={
                            "song": args.song,
                            "playlist": getattr(args, "playlist", None),
                            "output_dir": getattr(args, "output_dir", None),
                            "format": getattr(args, "format", "mp3"),
                            "bitrate": getattr(args, "bitrate", "auto"),
                        },
                    )

                    return processor.player_processor.download_song(
                        args.song,
                        getattr(args, "playlist", None),
                        getattr(args, "output_dir", None),
                        getattr(args, "format", "mp3"),
                        getattr(args, "bitrate", "auto"),
                    )

            case "playlist":
                from aurras.utils.command.processors import processor

                with logger.operation_context(
                    operation="playlist_command", subcommand="playlist"
                ):
                    operation_type = "play"
                    if getattr(args, "download", False):
                        operation_type = "download"
                    elif getattr(args, "delete", False):
                        operation_type = "delete"
                    elif getattr(args, "import", False):
                        operation_type = "import"
                    elif getattr(args, "search", False):
                        operation_type = "search"
                    elif getattr(args, "list", False):
                        operation_type = "list"

                    logger.debug(
                        "Executing playlist command",
                        extra={
                            "playlist_name": args.name,
                            "operation_type": operation_type,
                            "shuffle": getattr(args, "shuffle", False),
                            "no_lyrics": getattr(args, "no_lyrics", False),
                        },
                    )

                    if getattr(args, "download", False):
                        return processor.playlist_processor.download_playlist(
                            args.name,
                            getattr(args, "format", None),
                            getattr(args, "bitrate", None),
                        )
                    elif getattr(args, "delete", False):
                        return processor.playlist_processor.delete_playlist(args.name)
                    elif getattr(args, "import", False):
                        return processor.spotify_processor.import_user_playlists()
                    elif getattr(args, "search", False):
                        return processor.playlist_processor.search_playlists(args.name)
                    elif getattr(args, "list", False):
                        return processor.playlist_processor.view_playlist(args.name)
                    else:
                        return processor.playlist_processor.play_playlist(
                            args.name,
                            not getattr(args, "no_lyrics", False),
                            getattr(args, "shuffle", False),
                        )

            case "history":
                from aurras.utils.command.processors import processor

                with logger.operation_context(
                    operation="history_command", subcommand="history"
                ):
                    operation_type = "show"
                    if getattr(args, "clear", False):
                        operation_type = "clear"
                    elif getattr(args, "previous", False):
                        operation_type = "previous"

                    logger.debug(
                        "Executing history command",
                        extra={
                            "operation_type": operation_type,
                            "limit": getattr(args, "limit", 30),
                        },
                    )

                    if getattr(args, "clear", False):
                        return processor.history_processor.clear_history()
                    elif getattr(args, "previous", False):
                        return processor.history_processor.play_previous_song()
                    else:
                        return processor.history_processor.show_history(
                            getattr(args, "limit", 30)
                        )

            case "settings":
                from aurras.utils.command.processors import processor

                with logger.operation_context(
                    operation="settings_command", subcommand="settings"
                ):
                    operation_type = "list"
                    if getattr(args, "set", None):
                        operation_type = "set"
                    elif getattr(args, "reset", False):
                        operation_type = "reset"

                    logger.debug(
                        "Executing settings command",
                        extra={
                            "operation_type": operation_type,
                            "setting_key": args.set[0]
                            if getattr(args, "set", None)
                            else None,
                        },
                    )

                    if getattr(args, "list", False):
                        return processor.settings_processor.list_settings()
                    elif getattr(args, "set", None):
                        key, value = args.set
                        return processor.settings_processor.set_setting(key, value)
                    elif getattr(args, "reset", False):
                        return processor.settings_processor.reset_settings()
                    else:
                        return processor.settings_processor.list_settings()

            case "theme":
                from aurras.utils.command.processors import processor

                with logger.operation_context(
                    operation="theme_command", subcommand="theme"
                ):
                    operation_type = "set" if args.name else "list"

                    logger.debug(
                        "Executing theme command",
                        extra={
                            "operation_type": operation_type,
                            "theme_name": args.name,
                        },
                    )

                    if getattr(args, "list", False):
                        return processor.theme_processor.list_themes()
                    elif args.name:
                        return processor.theme_processor.set_theme(args.name)
                    else:
                        return processor.theme_processor.list_themes()

            case "setup":
                from aurras.utils.command.processors import processor

                with logger.operation_context(
                    operation="setup_command", subcommand="setup"
                ):
                    service = "spotify" if getattr(args, "spotify", False) else None
                    operation_type = "setup"
                    if getattr(args, "status", False):
                        operation_type = "status"
                    elif getattr(args, "reset", False):
                        operation_type = "reset"

                    logger.debug(
                        "Executing setup command",
                        extra={"service": service, "operation_type": operation_type},
                    )

                    if getattr(args, "spotify", False):
                        if getattr(args, "status", False):
                            return processor.spotify_processor.check_spotify_status()
                        elif getattr(args, "reset", False):
                            return (
                                processor.spotify_processor.reset_spotify_credentials()
                            )
                        else:
                            return processor.spotify_processor.setup_spotify()
                    elif getattr(args, "status", False) or getattr(
                        args, "reset", False
                    ):
                        console.print_error(
                            "Please specify a service (e.g., --spotify) with --status or --reset"
                        )
                        return 1
                    else:
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
                from aurras.utils.command.processors import processor

                with logger.operation_context(
                    operation="backup_command", subcommand="backup"
                ):
                    operation_type = "list"
                    if getattr(args, "create", False):
                        operation_type = "create"
                    elif getattr(args, "delete", False):
                        operation_type = "delete"
                    elif getattr(args, "restore", None) is not None:
                        operation_type = "restore"

                    logger.debug(
                        "Executing backup command",
                        extra={
                            "operation_type": operation_type,
                            "backup_id": getattr(args, "delete", None)
                            or getattr(args, "restore", None),
                        },
                    )

                    if getattr(args, "list", False):
                        return processor.backup_processor.list_backups()
                    elif getattr(args, "create", False):
                        return processor.backup_processor.create_backup(args.create)
                    elif getattr(args, "delete", False):
                        return processor.backup_processor.delete_backup(args.delete)
                    elif getattr(args, "restore", None) is not None:
                        return processor.backup_processor.restore_backup(args.restore)
                    else:
                        return processor.backup_processor.list_backups()

            case "self":
                from aurras.utils.command.processors import processor

                with logger.operation_context(
                    operation="self_command", subcommand="self"
                ):
                    operation_type = "info"
                    if getattr(args, "uninstall", False):
                        operation_type = "uninstall"
                    elif getattr(args, "check", False):
                        operation_type = "check"

                    logger.debug(
                        "Executing self command",
                        extra={"operation_type": operation_type},
                    )

                    if getattr(args, "uninstall", False):
                        return processor.self_processor.uninstall()
                    elif getattr(args, "info", False):
                        return processor.self_processor.get_version_info()
                    elif getattr(args, "check", False):
                        return processor.self_processor.check_dependencies()
                    else:
                        return processor.self_processor.get_version_info()

        # If we got here with no subcommand, show help
        if not subcommand:
            logger.info("No subcommand specified, showing help")
            parser.print_help()
            return 0

    except KeyboardInterrupt:
        logger.info("User interrupted execution")
        console.print_success("Thanks for using Aurras!")
        return 0

    except Exception as e:
        logger.error(
            "Unhandled exception in main",
            extra={"error_type": type(e).__name__, "error_message": str(e)},
            exc_info=True,
        )
        console.print_error(f"An error occurred: {str(e)}")
        return 1

    logger.debug("Aurras CLI completed successfully")
    return 0


if __name__ == "__main__":
    with logger.profile_context("full_cli_execution"):
        exit_code = main()
        sys.exit(exit_code)
