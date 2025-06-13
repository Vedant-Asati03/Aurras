"""
Spotify Credentials Cache Loader

This module provides functionality for loading Spotify credentials and tokens,
following the Aurras loader pattern.
"""

import json
from typing import Optional, Dict

from aurras.utils.logger import get_logger
from aurras.utils.path_manager import _path_manager

logger = get_logger("aurras.services.spotify.cache.loader", log_to_console=False)


class SpotifyCredentialsLoader:
    """
    Handles loading Spotify credentials and cached tokens.
    
    This class follows the Aurras pattern for cache loaders,
    providing read-only operations for credential data.
    """

    def __init__(self):
        """Initialize the credentials loader."""

    def load_credentials(self) -> Optional[Dict[str, str]]:
        """
        Load Spotify credentials from storage.

        Returns:
            dict: The loaded credentials or None if not found/failed
        """
        try:
            with open(_path_manager.credentials_file, "r") as credentials_file:
                credentials = json.load(credentials_file)
                logger.debug("Credentials loaded successfully")
                return credentials

        except FileNotFoundError:
            logger.warning("Credentials file not found")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from credentials file: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading credentials: {e}")
            return None

    def validate_credentials(self, credentials: Optional[Dict[str, str]]) -> bool:
        """
        Validate that credentials contain required fields.

        Args:
            credentials: The credentials dictionary to validate

        Returns:
            bool: True if credentials are valid
        """
        if not credentials:
            return False
            
        required_fields = ["client_id", "client_secret"]
        return all(
            field in credentials and credentials[field].strip()
            for field in required_fields
        )

    def credentials_exist(self) -> bool:
        """
        Check if credentials file exists and is readable.

        Returns:
            bool: True if credentials file exists
        """
        try:
            return _path_manager.credentials_file.exists()
        except Exception as e:
            logger.error(f"Error checking credentials file existence: {e}")
            return False
