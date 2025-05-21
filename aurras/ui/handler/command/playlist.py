"""
Playlist commands for Aurras Music Player.

This module contains all playlist-related commands such as create, delete, view, and play playlists.
"""

from aurras.core.settings import SETTINGS
from aurras.utils.logger import get_logger
from aurras.ui.core.registry import command_registry
from aurras.utils.command.processors import spotify_processor
from aurras.utils.command.processors import playlist_processor

logger = get_logger("aurras.ui.handler.command.playlist", log_to_console=False)
COMMAND_SETTINGS = SETTINGS.command


def register_playlist_commands():
    """Register all playlist-related commands to the central registry."""
    command_registry.register_command(
        name=COMMAND_SETTINGS.play_playlist,
        function=playlist_processor.play_playlist,
        description="Play a playlist",
        parameter_help="<playlist_name>",
        requires_args=True,
        category="Playlist",
    )

    command_registry.register_command(
        name=COMMAND_SETTINGS.download_playlist,
        function=playlist_processor.download_playlist,
        description="Download a playlist",
        parameter_help="<playlist_name>",
        requires_args=True,
        category="Download",
    )

    command_registry.register_command(
        name=COMMAND_SETTINGS.view_playlist,
        function=playlist_processor.view_playlist,
        description="View playlist contents",
        parameter_help="<playlist_name>",
        requires_args=True,
        category="Playlist",
    )

    command_registry.register_command(
        name=COMMAND_SETTINGS.delete_playlist,
        function=playlist_processor.delete_playlist,
        description="Delete a playlist",
        parameter_help="<playlist_name>",
        requires_args=True,
        category="Playlist",
    )

    command_registry.register_command(
        name=COMMAND_SETTINGS.import_playlist,
        function=spotify_processor.import_user_playlists,
        description="Import a playlist from Spotify",
        parameter_help="<playlist_name>",
        requires_args=False,
        category="Playlist",
    )

    command_registry.register_command(
        name=COMMAND_SETTINGS.search_by_song_or_artist,
        function=playlist_processor.search_playlists,
        description="Search for a playlist",
        parameter_help="<song_or_artist_name>",
        requires_args=True,
        category="Playlist",
    )

    logger.debug("Playlist commands registered")
