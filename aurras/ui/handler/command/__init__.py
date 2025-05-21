"""
Command modules for Aurras Music Player.

This package contains domain-specific command modules organized by functionality:
- player_commands: Commands for playback and song management
- playlist_commands: Commands for playlist operations
- history_commands: Commands for history management
- system_commands: Commands for system settings and cache management
- spotify_commands: Commands for Spotify integration
"""

from aurras.utils.logger import get_logger
from aurras.ui.handler.command.theme import register_theme_commands
from aurras.ui.handler.command.player import register_player_commands
from aurras.ui.handler.command.system import register_system_commands
from aurras.ui.handler.command.history import register_history_commands
from aurras.ui.handler.command.spotify import register_spotify_commands
from aurras.ui.handler.command.settings import register_settings_commands
from aurras.ui.handler.command.playlist import register_playlist_commands

logger = get_logger("aurras.ui.handler.command", log_to_console=False)


def register_all_commands():
    """Register all commands from all command modules."""
    register_theme_commands()
    logger.debug("Theme commands registered")
    register_player_commands()
    logger.debug("Player commands registered")
    register_system_commands()
    logger.debug("System commands registered")
    register_history_commands()
    logger.debug("History commands registered")
    register_spotify_commands()
    logger.debug("Spotify commands registered")
    register_settings_commands()
    logger.debug("Settings commands registered")
    register_playlist_commands()
    logger.debug("Playlist commands registered")
