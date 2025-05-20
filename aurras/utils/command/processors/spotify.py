"""
Spotify service processor for Aurras CLI.

This module handles Spotify-related commands and operations such as
authentication and service configuration.
"""

from aurras.utils.console import console
from aurras.utils.logger import get_logger
from aurras.utils.decorators import with_error_handling

logger = get_logger("aurras.command.processors.spotify", log_to_console=False)


class SpotifyProcessor:
    """Handle Spotify-related commands and operations."""

    def __init__(self):
        """Initialize the Spotify processor."""
        pass

    @with_error_handling
    def setup_spotify(self) -> int:
        """
        Set up Spotify API credentials.

        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        from aurras.services.spotify.setup import SpotifySetup

        # Show a themed panel with instructions
        instruction_panel = console.create_panel(
            "You'll need to authenticate with Spotify to import your playlists and favorites.",
            title="Spotify Setup",
            style="info",
        )
        console.print(instruction_panel)

        spotify_setup_handler = SpotifySetup()

        # Use the progress method from ThemedConsole
        with console.status(
            console.style_text(
                "Setting up Spotify authentication...", "primary", bold=True
            ),
            spinner="dots",
        ):
            result = spotify_setup_handler.setup_credentials()

        if not result:
            console.print_error("Failed to set up Spotify API credentials.")
            return 1

        console.print_success("Spotify API credentials set up successfully!")
        return 0

    @with_error_handling
    def import_user_playlists(self) -> int:
        """
        Import user playlists from Spotify.

        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        from aurras.services.spotify.fetcher import SpotifyUserDataRetriever

        # Show styled info message while working
        console.print_info("Starting import of Spotify playlists...")

        # Create a progress bar for playlist import
        progress = console.create_progress()

        with progress:
            task = progress.add_task("Importing playlists", total=100)

            # Use a progress callback that the fetcher can call
            def update_progress(percent):
                progress.update(task, completed=percent)

            fetcher = SpotifyUserDataRetriever()
            available_playlists = fetcher.retrieve_user_playlists(
                progress_callback=update_progress
            )

        if not available_playlists:
            console.print_warning("No playlists found or import failed.")
            return 1

        # Create a table to display the imported playlists
        table = console.create_table("Imported Spotify Playlists")
        table.add_column("Name")
        table.add_column("Tracks")

        for playlist in available_playlists[:10]:  # Show first 10 playlists
            table.add_row(
                playlist.get("name", "Unknown"), str(len(playlist.get("tracks", [])))
            )

        if len(available_playlists) > 10:
            table.add_row("...", f"+ {len(available_playlists) - 10} more")

        console.print(table)
        console.print_success(
            f"Successfully imported {len(available_playlists)} playlists"
        )
        return 0
