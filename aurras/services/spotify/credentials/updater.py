"""
Spotify Credentials Cache Updater

This module provides functionality for storing Spotify credentials and tokens,
following the Aurras updater pattern.
"""

import json
from typing import Dict

from aurras.utils.logger import get_logger
from aurras.utils.path_manager import _path_manager

logger = get_logger("aurras.services.spotify.cache.updater", log_to_console=False)


class SpotifyCredentialsUpdater:
    """
    Handles storing and updating Spotify credentials and cached tokens.
    
    This class follows the Aurras pattern for cache updaters,
    providing write operations for credential data.
    """

    def __init__(self):
        """Initialize the credentials updater."""

    def store_credentials(self, credentials: Dict[str, str]) -> bool:
        """
        Save Spotify credentials to storage.

        Args:
            credentials: Dictionary containing client_id and client_secret

        Returns:
            bool: True if credentials were stored successfully
        """
        try:
            # Ensure the directory exists
            _path_manager.credentials_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(_path_manager.credentials_file, "w") as credentials_file:
                json.dump(credentials, credentials_file, indent=2)
            
            logger.info("Credentials stored successfully")
            return True

        except Exception as e:
            logger.error(f"Error storing credentials: {e}")
            return False

    def update_credentials(self, updates: Dict[str, str]) -> bool:
        """
        Update existing credentials with new values.

        Args:
            updates: Dictionary containing fields to update

        Returns:
            bool: True if update was successful
        """
        from .loader import SpotifyCredentialsLoader
        
        loader = SpotifyCredentialsLoader()
        existing_credentials = loader.load_credentials() or {}
        
        # Merge updates with existing credentials
        existing_credentials.update(updates)
        
        return self.store_credentials(existing_credentials)

    def reset_credentials(self) -> bool:
        """
        Remove stored credentials.

        Returns:
            bool: True if credentials were reset successfully
        """
        try:
            if _path_manager.credentials_file.exists():
                _path_manager.credentials_file.unlink()
                logger.info("Credentials reset successfully")
            else:
                logger.info("No credentials file to reset")
            return True

        except Exception as e:
            logger.error(f"Error resetting credentials: {e}")
            return False
