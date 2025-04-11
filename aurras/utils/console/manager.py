"""
Console manager for terminal UI rendering.

This module provides utilities for working with the terminal console
and accessing theme information for rendering.
"""

import logging
from typing import Optional
from rich.console import Console

from ...themes import get_theme, get_current_theme, set_current_theme
from ...themes.adapters import theme_to_rich_theme

logger = logging.getLogger(__name__)

# Global console instance for consistent styling
_console: Optional[Console] = None


def get_console() -> Console:
    """
    Get or create a global console instance with the current theme.

    Returns:
        Configured Rich console
    """
    global _console

    # Initialize console with current theme if needed
    if not _console:
        _console = create_themed_console()

    return _console


def create_themed_console(theme_name: Optional[str] = None) -> Console:
    """
    Create a new Rich console with the specified theme.

    Args:
        theme_name: Name of theme to use, or None for current theme

    Returns:
        New Rich console with the theme applied
    """
    # Get theme from unified theme system
    if theme_name is None:
        theme_name = get_current_theme()

    theme_def = get_theme(theme_name)

    # Convert to Rich theme
    rich_theme = theme_to_rich_theme(theme_def)

    # Create and return the console
    return Console(
        theme=rich_theme,
        highlight=True,
        emoji=True,
        width=None,  # Allow automatic width detection
    )


def update_console_theme(theme_name: Optional[str] = None) -> None:
    """
    Update the global console's theme.

    Args:
        theme_name: Name of theme to use, or None for current theme
    """
    global _console

    # Create a new console with the theme
    _console = create_themed_console(theme_name)


def change_theme(theme_name: str) -> bool:
    """
    Change the current theme and update the console.

    This function both updates the theme in the theme system
    and refreshes the console to use the new theme.

    Args:
        theme_name: Name of the theme to set

    Returns:
        True if successful, False otherwise
    """
    try:
        # Set the theme in the theme system
        success = set_current_theme(theme_name)

        if success:
            # Update the console to use the new theme
            update_console_theme(theme_name)
            logger.info(f"Theme changed to {theme_name}")
            return True
        else:
            logger.warning(f"Failed to set theme {theme_name}")
            return False
    except Exception as e:
        logger.error(f"Error changing theme: {e}")
        return False


def get_available_themes() -> list[str]:
    """
    Get a list of available theme names.

    Returns:
        List of theme names
    """
    from ...themes import get_available_themes as get_themes

    return get_themes()
