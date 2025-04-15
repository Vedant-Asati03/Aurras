"""
Initialization Module

This module handles application initialization tasks.
"""

import logging

from ..core.settings import load_settings
from .path_manager import PathManager

_path_manager = PathManager()

logger = logging.getLogger(__name__)


def initialize_application():
    """
    Initialize the application by setting up necessary directories and files.

    This should be called at the start of the application to ensure all
    required directories exist and default settings are in place.
    """
    try:
        logger.info("Initializing application environment")
        # Create necessary directories
        _path_manager.create_required_directories()

        if not _path_manager.settings_file.exists():
            # Load settings will handle creating the default settings file
            load_settings()
            logger.info("Created default settings file")

        logger.info("Application initialization completed successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        return False
