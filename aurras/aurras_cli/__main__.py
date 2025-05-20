"""
Main execution module for Aurras.

This module allows running Aurras as a module via `python -m aurras`.
"""

from aurras.utils.logger import get_logger
from aurras.utils.command.dispatcher import main

logger = get_logger("aurras.__main__", log_to_console=False)

if __name__ == "__main__":
    logger.debug("Aurras CLI started as a module.")
    main()
    logger.debug("Aurras CLI finished execution.")
