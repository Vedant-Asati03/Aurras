"""
Spotify Credentials Module

This module provides database operations for Spotify credentials and tokens,
following the Aurras cache pattern used in core/cache and core/playlist/cache.
"""

from .loader import SpotifyCredentialsLoader
from .updater import SpotifyCredentialsUpdater

from aurras.utils.logger import get_logger

logger = get_logger("aurras.services.spotify.cache", log_to_console=False)

__all__ = [
    "SpotifyCredentialsLoader",
    "SpotifyCredentialsUpdater",
]
