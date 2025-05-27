"""
Theme management for Aurras.

This module provides functions to select, retrieve, and manage themes
used throughout the application. It serves as the central point for
theme related operations.
"""

from typing import Dict, List, Optional, Union

from aurras.utils.logger import get_logger
from aurras.themes.definitions import ThemeDefinition, ThemeCategory
from aurras.themes.themes import AVAILABLE_THEMES, get_default_theme_from_settings

logger = get_logger("aurras.themes.manager", log_to_console=False)

_current_theme = get_default_theme_from_settings()


def get_theme(theme_name: Optional[str] = None) -> ThemeDefinition:
    """
    Get a theme by name, or the current theme if no name provided.

    Args:
        theme_name: Name of the theme to retrieve, or None for current theme

    Returns:
        The requested theme definition

    Raises:
        KeyError: If the theme does not exist
    """
    if theme_name is None:
        theme_name = get_current_theme()

    theme_name_upper = theme_name.upper()
    if theme_name_upper in AVAILABLE_THEMES:
        return AVAILABLE_THEMES[theme_name_upper]

    # Try to find a case-insensitive match
    for key in AVAILABLE_THEMES.keys():
        if key.lower() == theme_name.lower():
            return AVAILABLE_THEMES[key]

    raise KeyError(f"Theme '{theme_name}' not found")


def get_available_themes() -> List[str]:
    """
    Get a list of all available theme names.

    Returns:
        List of theme names
    """
    return list(AVAILABLE_THEMES.keys())


def set_current_theme(theme_name: str) -> bool:
    """
    Set the current theme.

    Args:
        theme_name: Name of the theme to set

    Returns:
        True if successful, False otherwise
    """
    global _current_theme

    try:
        _current_theme = theme_name.upper()
        logger.info(f"Current theme set to {_current_theme}")
        return True
    except KeyError:
        logger.warning(f"Cannot set theme '{theme_name}': Theme not found")
        return False


def get_current_theme() -> str:
    """
    Get the name of the current theme.

    Returns:
        Current theme name
    """
    return _current_theme


def get_themes_by_category(
    category: Union[str, ThemeCategory],
) -> Dict[str, ThemeDefinition]:
    """
    Get themes filtered by category.

    Args:
        category: Category name or enum value to filter by

    Returns:
        Dictionary of theme names to theme definitions in the specified category
    """
    result = {}

    # Convert string to enum if needed
    if isinstance(category, str):
        try:
            category_enum = ThemeCategory[category.upper()]
        except KeyError:
            logger.warning(f"Invalid category: {category}")
            return result
    else:
        category_enum = category

    # Filter themes by category
    for name, theme in AVAILABLE_THEMES.items():
        if theme.category == category_enum:
            result[name] = theme

    return result
