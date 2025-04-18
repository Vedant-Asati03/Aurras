"""
Playlist commands for Aurras Music Player.

This module contains all playlist-related commands such as create, delete, view, and play playlists.
"""

import logging
from ...core.registry.command import CommandRegistry
from ....core.settings import load_settings
from ....utils.command.processors.playlist import processor

logger = logging.getLogger(__name__)
COMMAND_SETTINGS = load_settings().command


def register_playlist_commands(registry: CommandRegistry):
    """Register all playlist-related commands to the central registry."""
    registry.register_command(
        name=COMMAND_SETTINGS.play_playlist,
        function=processor.play_playlist,
        description="Play a playlist",
        parameter_help="<playlist_name>",
        requires_args=True,
        category="Playlist",
    )

    registry.register_command(
        name=COMMAND_SETTINGS.download_playlist,
        function=processor.download_playlist,
        description="Download a playlist",
        parameter_help="<playlist_name>",
        requires_args=True,
        category="Download",
    )

    registry.register_command(
        name=COMMAND_SETTINGS.view_playlist,
        function=processor.view_playlist,
        description="View playlist contents",
        parameter_help="<playlist_name>",
        requires_args=True,
        category="Playlist",
    )

    registry.register_command(
        name=COMMAND_SETTINGS.delete_playlist,
        function=processor.delete_playlist,
        description="Delete a playlist",
        parameter_help="<playlist_name>",
        requires_args=True,
        category="Playlist",
    )

    registry.register_command(
        name=COMMAND_SETTINGS.import_playlist,
        function=processor.import_playlist,
        description="Import a playlist from Spotify",
        parameter_help="[playlist_name]",
        requires_args=False,
        category="Playlist",
    )

    registry.register_command(
        name=COMMAND_SETTINGS.search_by_song_or_artist,
        function=processor.search_playlists,
        description="Search for a playlist",
        parameter_help="<song_or_artist_name>",
        requires_args=True,
        category="Playlist",
    )

    logger.debug("Playlist commands registered")
