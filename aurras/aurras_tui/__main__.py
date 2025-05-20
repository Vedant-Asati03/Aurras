"""
TUI entry point for Aurras Music Player.

This module provides the entry point for the textual-based TUI mode.
"""

import argparse
from pathlib import Path

from aurras.tui.app import AurrasTUI
from aurras.utils.path_manager import PathManager
from aurras.utils.logger import get_logger

logger = get_logger("aurras.tui.main", log_to_console=True)


def setup_tui():
    """Perform any setup needed before starting the TUI."""
    # Ensure paths are correctly set up
    path_manager = PathManager()

    # Add the styles directory to the search path
    # Textual looks for CSS files relative to the working directory or in specific locations
    styles_dir = Path(__file__).parent / "tui" / "styles"

    # Create the styles directory if it doesn't exist
    styles_dir.mkdir(parents=True, exist_ok=True)

    # Copy base.tcss to the styles directory if it doesn't exist
    base_css_path = styles_dir / "base.tcss"
    if not base_css_path.exists():
        source_css_path = Path(__file__).parent / "tui" / "styles" / "base.tcss"
        if source_css_path.exists():
            with open(source_css_path, "r") as src, open(base_css_path, "w") as dst:
                dst.write(src.read())
        else:
            # If source doesn't exist, create a minimal base CSS
            with open(base_css_path, "w") as f:
                f.write("/* Aurras TUI base styles */\n")


def main():
    """Entry point for Aurras TUI mode."""
    parser = argparse.ArgumentParser(description="Aurras Music Player TUI")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    # Setup TUI environment
    setup_tui()

    # Configure logging if in debug mode
    if args.debug:
    #     level=logging.DEBUG,
    #     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        logger.debug("Debug mode enabled")
        logger.debug("Starting Aurras TUI in debug mode")

    # Start the TUI application
    app = AurrasTUI()
    app.run()


if __name__ == "__main__":
    main()
