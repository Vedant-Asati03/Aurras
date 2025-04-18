"""
Command modules for Aurras Music Player.

This package contains domain-specific command modules organized by functionality:
- player_commands: Commands for playback and song management
- playlist_commands: Commands for playlist operations
- history_commands: Commands for history management
- system_commands: Commands for system settings and cache management
- spotify_commands: Commands for Spotify integration
"""

from .player import register_player_commands
from .system import register_system_commands
from .history import register_history_commands
from .spotify import register_spotify_commands
from .playlist import register_playlist_commands
from ...core.registry import CommandRegistry


def register_all_commands(registry: CommandRegistry):
    """Register all commands from all command modules."""
    register_player_commands(registry)
    register_system_commands(registry)
    register_history_commands(registry)
    register_spotify_commands(registry)
    register_playlist_commands(registry)
