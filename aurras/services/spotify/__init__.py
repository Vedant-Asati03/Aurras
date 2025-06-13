"""
Spotify Service Module

This module provides functionality for Spotify integration with Aurras,
including authentication, playlist importing, and API interactions.
"""

from .service import SpotifyService
from .auth import SpotifyAuth
from .api import SpotifyDataRetriever
from .cache import SpotifyCredentialsCache

__all__ = [
    "SpotifyService",
    "SpotifyAuth",
    "SpotifyDataRetriever",
    "SpotifyCredentialsCache",
    # Legacy exports for backward compatibility
    "SpotifySetup",
    "SpotifyClientService",
    "SpotifyUserDataRetriever",
    "CredentialsCache",
    "SpotifyOAuthHandler",
]


# Legacy imports for backward compatibility - only create when accessed
def __getattr__(name):
    if name == "SpotifySetup":
        return SpotifyAuth
    elif name == "SpotifyClientService":
        return SpotifyAuth
    elif name == "SpotifyUserDataRetriever":
        return SpotifyDataRetriever
    elif name == "CredentialsCache":
        return SpotifyCredentialsCache
    elif name == "SpotifyOAuthHandler":
        return SpotifyAuth
    else:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
