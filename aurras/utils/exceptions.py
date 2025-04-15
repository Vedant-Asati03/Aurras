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


class PlayerError(AurrasError):
    """Base exception for player-related errors."""

    pass


class LyricsError(PlayerError):
    """Exception raised when there's an issue with lyrics retrieval or processing."""

    pass


class MetadataError(PlayerError):
    """Exception raised when there's an issue with retrieving or processing metadata."""

    pass


class DisplayError(PlayerError):
    """Exception raised when there's an issue with the player display."""

    pass


class NetworkError(AurrasError):
    """Exception raised when there's a network connectivity issue."""

    pass


class StreamingError(PlaybackError):
    """Exception raised when there's an issue with streaming content."""

    pass


class DownloadError(AurrasError):
    """Exception raised when there's an issue downloading content."""

    pass


class LibraryError(AurrasError):
    """Exception raised when there's an issue with an external library dependency."""

    pass


class MPVLibraryError(LibraryError):
    """Exception raised when there's an issue with the MPV library."""

    pass


class DatabaseError(AurrasError):
    """Exception raised when there's an issue with database operations."""

    pass


class APIError(AurrasError):
    """Exception raised when there's an issue with an external API."""

    pass


class SpotifyAPIError(APIError):
    """Exception raised when there's an issue with the Spotify API."""

    pass


class CommandError(AurrasError):
    """Exception raised when there's an issue with command processing."""

    pass


class MemoryError(AurrasError):
    """Exception raised when there's an issue with memory management."""

    pass


class CacheError(AurrasError):
    """Exception raised when there's an issue with caching."""

    pass


class BackupError(AurrasError):
    """Exception raised when there's an issue with backup or restore operations."""

    pass


class ThemeError(AurrasError):
    """Exception raised when there's an issue with theme management."""

    pass


class TimeoutError(AurrasError):
    """Exception raised when an operation times out."""

    pass


class InvalidInputError(AurrasError):
    """Exception raised when user input is invalid."""

    pass
