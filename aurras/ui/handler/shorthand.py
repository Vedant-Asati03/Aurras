"""
Shorthand registry initialization for Aurras Music Player.

This module handles the registration of all shorthand commands in the application.
"""

import logging

from ..core.registry.shortcut import ShortcutRegistry
from ...core.settings import load_settings

logger = logging.getLogger(__name__)
COMMAND_SETTINGS = load_settings().command
SHORTHAND_SETTINGS = load_settings().shorthand


def register_default_shorthands(registry: ShortcutRegistry):
    """Register all default shorthand commands."""
    registry.clear()

    registry.register_shorthand(
        prefix=SHORTHAND_SETTINGS.download_song,
        command=COMMAND_SETTINGS.download_song,
        description="Download song (shorthand)",
        strip_prefix=True,
    )

    registry.register_shorthand(
        prefix=SHORTHAND_SETTINGS.play_offline,
        command=COMMAND_SETTINGS.play_offline,
        description="Localplayback (shorthand)",
        strip_prefix=False,
    )

    registry.register_shorthand(
        prefix=SHORTHAND_SETTINGS.play_previous_song,
        command=COMMAND_SETTINGS.play_previous_song,
        description="Play previous song (shorthand)",
        strip_prefix=True,
    )

    registry.register_shorthand(
        prefix=SHORTHAND_SETTINGS.play_playlist,
        command=COMMAND_SETTINGS.play_playlist,
        description="Play playlist (shorthand)",
        strip_prefix=True,
    )

    registry.register_shorthand(
        prefix=SHORTHAND_SETTINGS.download_playlist,
        command=SHORTHAND_SETTINGS.download_playlist,
        description="Download playlist (shorthand)",
        strip_prefix=True,
    )

    registry.register_shorthand(
        prefix=SHORTHAND_SETTINGS.view_playlist,
        command=COMMAND_SETTINGS.view_playlist,
        description="View playlist contents (shorthand)",
        strip_prefix=True,
    )

    registry.register_shorthand(
        prefix=SHORTHAND_SETTINGS.delete_playlist,
        command=COMMAND_SETTINGS.delete_playlist,
        description="Delete playlist (shorthand)",
        strip_prefix=True,
    )

    registry.register_shorthand(
        prefix=SHORTHAND_SETTINGS.display_history,
        command=COMMAND_SETTINGS.display_history,
        description="Display listening history (shorthand)",
        strip_prefix=True,
    )

    registry.register_shorthand(
        prefix=SHORTHAND_SETTINGS.toggle_lyrics,
        command=COMMAND_SETTINGS.toggle_lyrics,
        description="Toggle lyrics (shorthand)",
        strip_prefix=True,
    )

    logger.debug("Default shorthand commands registered")
