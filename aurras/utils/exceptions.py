"""
Exceptions Module

This module defines custom exceptions used throughout the Aurras application.
"""


class AurrasError(Exception):
    """Base exception for all Aurras errors."""

    pass


class PlaybackError(AurrasError):
    """Exception raised when a playback error occurs."""

    pass


class PlaylistError(AurrasError):
    """Base exception for playlist-related errors."""

    pass


class PlaylistNotFoundError(PlaylistError):
    """Exception raised when a playlist is not found."""

    pass


class SongsNotFoundError(AurrasError):
    """Exception raised when songs are not found."""

    pass


class AuthenticationError(AurrasError):
    """Base exception for authentication-related errors."""

    pass


class NotAuthenticatedError(AuthenticationError):
    """Exception raised when a user is not authenticated."""

    pass


class ConfigurationError(AurrasError):
    """Exception raised when there's a configuration issue."""

    pass
