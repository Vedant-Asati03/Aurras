"""
Spotify Credentials Cache

This module provides a unified interface for Spotify credentials cache operations,
combining loader and updater functionality following the Aurras cache pattern.
"""

from typing import Optional, Dict

from .credentials.loader import SpotifyCredentialsLoader
from .credentials.updater import SpotifyCredentialsUpdater


class SpotifyCredentialsCache:
    """
    Unified interface for Spotify credentials cache operations.

    This class combines the loader and updater functionality,
    providing a single interface for credential management.
    """

    def __init__(self):
        """Initialize the credentials cache."""
        self._loader = SpotifyCredentialsLoader()
        self._updater = SpotifyCredentialsUpdater()

    # =====================
    # Read Operations (from loader)
    # =====================

    def load_credentials(self) -> Optional[Dict[str, str]]:
        """
        Load Spotify credentials from storage.

        Returns:
            dict: The loaded credentials or None if not found/failed
        """
        return self._loader.load_credentials()

    def validate_credentials(self, credentials: Optional[Dict[str, str]]) -> bool:
        """
        Validate that credentials contain required fields.

        Args:
            credentials: The credentials dictionary to validate

        Returns:
            bool: True if credentials are valid
        """
        return self._loader.validate_credentials(credentials)

    def credentials_exist(self) -> bool:
        """
        Check if credentials file exists and is readable.

        Returns:
            bool: True if credentials file exists
        """
        return self._loader.credentials_exist()

    # =====================
    # Write Operations (from updater)
    # =====================

    def store_credentials(self, credentials: Dict[str, str]) -> bool:
        """
        Save Spotify credentials to storage.

        Args:
            credentials: Dictionary containing client_id and client_secret

        Returns:
            bool: True if credentials were stored successfully
        """
        return self._updater.store_credentials(credentials)

    def update_credentials(self, updates: Dict[str, str]) -> bool:
        """
        Update existing credentials with new values.

        Args:
            updates: Dictionary containing fields to update

        Returns:
            bool: True if update was successful
        """
        return self._updater.update_credentials(updates)

    def reset_credentials(self) -> bool:
        """
        Remove stored credentials.

        Returns:
            bool: True if credentials were reset successfully
        """
        return self._updater.reset_credentials()

    # =====================
    # Convenience Methods
    # =====================

    def is_setup(self) -> bool:
        """
        Check if Spotify credentials are properly set up.

        Returns:
            bool: True if credentials exist and are valid
        """
        credentials = self.load_credentials()
        return self.validate_credentials(credentials)


# Legacy class name for backward compatibility
class CredentialsCache(SpotifyCredentialsCache):
    """Legacy class name - use SpotifyCredentialsCache instead."""

    pass
