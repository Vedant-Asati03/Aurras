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
        from aurras.services.spotify import SpotifyAuth

        spotify_setup_handler = SpotifyAuth()

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
        from aurras.services.spotify import SpotifyService

        service = SpotifyService()

        if not service.is_setup():
            console.print_warning(
                "Spotify not configured. Setting up Spotify integration..."
            )

            setup_result = self.setup_spotify()
            if setup_result != 0:
                console.print_error(
                    "Setup failed. Please run 'aurras setup --spotify' manually."
                )
                return 1

            console.print_info("Setup completed! Proceeding with playlist import...")

            service = SpotifyService()

        imported_playlists = service.import_playlists()

        if not imported_playlists:
            console.print_warning("No playlists found or import failed.")
            return 1

        console.print_success(
            f"Successfully imported {len(imported_playlists)} playlists"
        )
        return 0

    @with_error_handling
    def check_spotify_status(self) -> int:
        """
        Check Spotify integration status.

        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        from aurras.services.spotify import SpotifyService

        service = SpotifyService()

        if service.is_setup():
            console.print_success(" Spotify is configured and ready to use")

            user_info = service.get_user_info()
            if user_info:
                console.print_info(
                    f"Connected as: {user_info.get('display_name', 'Unknown')}"
                )
                console.print_info(f"User ID: {user_info.get('id', 'Unknown')}")
                console.print_success(" Connection to Spotify is working")
            else:
                console.print_warning(
                    " Credentials configured but connection test failed"
                )
                console.print_info(
                    "You may need to re-authenticate. Try: aurras setup --spotify"
                )
        else:
            console.print_error(" Spotify is not configured")
            console.print_info(
                "Run 'aurras setup --spotify' to configure Spotify integration"
            )

        return 0

    @with_error_handling
    def reset_spotify_credentials(self) -> int:
        """
        Reset Spotify credentials and authentication.

        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        from aurras.services.spotify import SpotifyService

        service = SpotifyService()

        success = service.reset_credentials()

        if success:
            return 0
        else:
            return 1
