"""
Shorthand registry initialization for Aurras Music Player.

This module handles the registration of all shorthand commands in the application.
"""

import logging
from ..core.registry.shortcut import ShortcutRegistry

logger = logging.getLogger(__name__)
shortcut_registry = ShortcutRegistry()


def register_default_shorthands():
    """Register all default shorthand commands."""
    shortcut_registry.clear()

    shortcut_registry.register_shorthand(
        prefix="v ",
        command="view_playlist",
        description="View playlist contents (shorthand)",
        strip_prefix=True,
    )

    shortcut_registry.register_shorthand(
        prefix="p ",
        command="play_playlist",
        description="Play playlist (shorthand)",
        strip_prefix=True,
    )

    shortcut_registry.register_shorthand(
        prefix="d ",
        command="download_song",
        description="Download song (shorthand)",
        strip_prefix=True,
    )

    logger.debug("Default shorthand commands registered")
