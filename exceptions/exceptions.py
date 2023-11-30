class PlaylistNotFoundError(Exception):
    """Exception raised when a playlist is not found."""


class SongsNotFoundError(Exception):
    """Exception raised when songs are not found."""


class NotAuthenticatedError(Exception):
    """Exception raised when a user is not authenticated."""
