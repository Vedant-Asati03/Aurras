"""
Theme management for Aurras.

This module provides functions to select, retrieve, and manage themes
used throughout the application. It serves as the central point for
theme related operations.
"""

import os
import json
from pathlib import Path
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
        get_theme(theme_name)
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


def load_theme_from_file(filepath: str) -> Optional[ThemeDefinition]:
    """
    Load a theme from a JSON file.

    Args:
        filepath: Path to the theme file

    Returns:
        Loaded theme, or None if loading failed
    """
    try:
        with open(filepath, "r") as f:
            theme_data = json.load(f)

        theme = ThemeDefinition.from_dict(theme_data)
        logger.info(f"Successfully loaded theme '{theme.name}' from {filepath}")
        return theme
    except (json.JSONDecodeError, IOError, ValueError) as e:
        logger.error(f"Failed to load theme from {filepath}: {e}")
        return None


def save_theme_to_file(theme: ThemeDefinition, filepath: str) -> bool:
    """
    Save a theme to a JSON file.

    Args:
        theme: Theme to save
        filepath: Path to save the theme file

    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)

        # Convert theme to dictionary
        theme_dict = theme.to_dict()

        # Write to file with pretty printing
        with open(filepath, "w") as f:
            json.dump(theme_dict, f, indent=2)

        logger.info(f"Successfully saved theme '{theme.name}' to {filepath}")
        return True
    except Exception as e:
        logger.error(f"Failed to save theme to {filepath}: {e}")
        return False


def discover_user_themes(themes_dir: Optional[str] = None) -> List[ThemeDefinition]:
    """
    Discover user-defined themes in the themes directory.

    Args:
        themes_dir: Directory to look for theme files, or None to use default

    Returns:
        List of discovered themes
    """
    if themes_dir is None:
        # Default to user's home directory .aurras/themes
        themes_dir = os.path.join(Path.home(), ".aurras", "themes")

    themes = []

    # Ensure the directory exists
    if not os.path.exists(themes_dir):
        logger.info(f"Themes directory {themes_dir} does not exist.")
        try:
            os.makedirs(themes_dir, exist_ok=True)
            logger.info(f"Created themes directory at {themes_dir}")
        except Exception as e:
            logger.error(f"Failed to create themes directory: {e}")
        return themes

    # Look for .json theme files
    for filename in os.listdir(themes_dir):
        if filename.endswith(".json"):
            filepath = os.path.join(themes_dir, filename)
            theme = load_theme_from_file(filepath)
            if theme:
                themes.append(theme)
                logger.info(f"Discovered user theme: {theme.name}")

    return themes


def register_user_theme(theme: ThemeDefinition) -> None:
    """
    Register a user theme so it can be used by the application.

    Args:
        theme: Theme to register
    """
    AVAILABLE_THEMES[theme.name] = theme
    logger.info(f"Registered theme '{theme.name}'")


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
