import json
import logging
from typing import Optional, Dict

from aurras.utils.path_manager import _path_manager

logger = logging.getLogger(__name__)


class CredentialsCache:
    def __init__(self):
        """Initialize the CredentialsCache with credentials."""

    def store_credentials(self, credentials: Dict[str, str]) -> bool:
        """
        Save the credentials to a file.

        Returns:
            bool: True if credentials were stored successfully, False otherwise
        """
        try:
            with open(_path_manager.credentials_file, "w") as credentials_file:
                json.dump(credentials, credentials_file)
            return True

        except Exception as e:
            logger.error(f"Error storing credentials: {e}")
            return False

    def load_credentials(self) -> Optional[Dict[str, str]]:
        """
        Load the credentials from a file.

        Returns:
            dict: The loaded credentials or an empty dictionary if failed
        """
        try:
            with open(_path_manager.credentials_file, "r") as credentials_file:
                return json.load(credentials_file)

        except FileNotFoundError:
            logger.warning("Credentials file not found.")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from credentials file: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error loading credentials: {e}")
            return {}

    def reset_credentials(self) -> bool:
        """
        Reset the credentials by deleting the file.

        Returns:
            bool: True if credentials were reset successfully, False otherwise
        """
        try:
            if _path_manager.credentials_file.exists():
                _path_manager.credentials_file.unlink()
                logger.info("Credentials file deleted successfully.")
                return True

        except Exception as e:
            logger.error(f"Error resetting credentials: {e}")
            return False
