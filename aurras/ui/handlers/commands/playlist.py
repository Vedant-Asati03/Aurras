"""
Playlist commands for Aurras Music Player.

This module contains all playlist-related commands such as create, delete, view, and play playlists.
"""

import logging
from ...core.registry.command import CommandRegistry
from ....utils.command.processors.playlist import processor

logger = logging.getLogger(__name__)
command_registry = CommandRegistry()


def register_playlist_commands():
    """Register all playlist-related commands to the central registry."""
    command_registry.register_command(
        name="play_playlist",
        function=processor.play_playlist,
        description="Play a playlist",
        parameter_help="<playlist_name>",
        requires_args=True,
        category="Playlist",
    )

    command_registry.register_command(
        name="download_playlist",
        function=processor.download_playlist,
        description="Download a playlist",
        parameter_help="<playlist_name>",
        requires_args=True,
        category="Download",
    )

    command_registry.register_command(
        name="view_playlist",
        function=processor.view_playlist,
        description="View playlist contents",
        parameter_help="<playlist_name>",
        requires_args=True,
        category="Playlist",
    )

    command_registry.register_command(
        name="delete_playlist",
        function=processor.delete_playlist,
        description="Delete a playlist",
        parameter_help="<playlist_name>",
        requires_args=True,
        category="Playlist",
    )

    command_registry.register_command(
        name="import_playlist",
        function=processor.import_playlist,
        description="Import a playlist from Spotify",
        parameter_help="[playlist_name]",
        requires_args=False,
        category="Playlist",
    )

    command_registry.register_command(
        name="Search_by_song",
        function=processor.search_playlists,
        description="Search for a playlist",
        parameter_help="<song_or_artist_name>",
        requires_args=True,
        category="Playlist",
    )

    logger.debug("Playlist commands registered")
