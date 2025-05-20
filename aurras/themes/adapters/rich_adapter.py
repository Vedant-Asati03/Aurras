"""
Rich console adapter for the Aurras theme system.

This module provides functionality to convert theme definitions
to Rich library compatible formats with optimized caching.
"""

from typing import Dict, List, Optional, Union, cast

from rich.style import Style
from rich.theme import Theme as RichTheme

from aurras.utils.logger import get_logger
from aurras.themes.definitions import ThemeDefinition
from aurras.themes.utils import get_fallback_value, ThemeValueCache

logger = get_logger("aurras.themes.adapters.rich_adapter", log_to_console=False)

# Caches for expensive theme conversions - use name as key instead of ThemeDefinition
_rich_theme_cache = ThemeValueCache[str, RichTheme]()
_gradient_cache = ThemeValueCache[str, Dict[str, List[str]]]()


def theme_to_rich_theme(theme_def: ThemeDefinition) -> RichTheme:
    """
    Convert a ThemeDefinition to a Rich Theme with optimized caching.

    Args:
        theme_def: The theme definition to convert

    Returns:
        A Rich Theme instance for console styling

    Example:
        >>> theme = get_theme("GALAXY")
        >>> rich_theme = theme_to_rich_theme(theme)
        >>> isinstance(rich_theme, RichTheme)
        True
    """
    # Use the theme name for the cache key instead of the ThemeDefinition object
    theme_name = theme_def.name

    # Use cache for better performance
    return _rich_theme_cache.get(theme_name, _compute_rich_theme, theme_def)


def _compute_rich_theme(theme_def: ThemeDefinition) -> RichTheme:
    """
    Internal function to compute a Rich theme from a ThemeDefinition.

    Args:
        theme_def: The theme definition to convert

    Returns:
        A newly computed Rich Theme instance
    """
    # Define the style mappings with fallbacks
    style_mapping = {
        # Basic color mappings
        "primary": (
            theme_def.primary.hex if theme_def.primary else None,
            [],
            "#FFFFFF",
        ),
        "secondary": (
            theme_def.secondary.hex if theme_def.secondary else None,
            [theme_def.primary.hex if theme_def.primary else None],
            "#CCCCCC",
        ),
        "accent": (
            theme_def.accent.hex if theme_def.accent else None,
            [
                theme_def.secondary.hex if theme_def.secondary else None,
                theme_def.primary.hex if theme_def.primary else None,
            ],
            "#AAAAAA",
        ),
        # Status colors
        "success": (
            theme_def.success.hex if theme_def.success else None,
            [
                theme_def.accent.hex if theme_def.accent else None,
                theme_def.primary.hex if theme_def.primary else None,
            ],
            "#00FF00",
        ),
        "warning": (
            theme_def.warning.hex if theme_def.warning else None,
            [],
            "#FFCC00",
        ),
        "error": (theme_def.error.hex if theme_def.error else None, [], "#FF0000"),
        "info": (
            theme_def.info.hex if theme_def.info else None,
            [theme_def.primary.hex if theme_def.primary else None],
            "#00BFFF",
        ),
        # UI element styles for playback
        "title": (
            f"bold {theme_def.primary.hex}" if theme_def.primary else None,
            [],
            "bold white",
        ),
        "artist": (
            theme_def.secondary.hex if theme_def.secondary else None,
            [theme_def.primary.hex if theme_def.primary else None],
            "#DDDDDD",
        ),
        "album": (
            theme_def.accent.hex if theme_def.accent else None,
            [
                theme_def.secondary.hex if theme_def.secondary else None,
                theme_def.primary.hex if theme_def.primary else None,
            ],
            "#BBBBBB",
        ),
        "duration": (theme_def.text.hex if theme_def.text else None, [], "#FFFFFF"),
        "playing": (
            f"bold {theme_def.success.hex}" if theme_def.success else None,
            [f"bold {theme_def.primary.hex}" if theme_def.primary else None],
            "bold green",
        ),
        "controls": (
            theme_def.accent.hex if theme_def.accent else None,
            [theme_def.primary.hex if theme_def.primary else None],
            "#FFFFFF",
        ),
        # Additional Rich-specific styles
        "header": (theme_def.primary.hex if theme_def.primary else None, [], "#FFFFFF"),
        "highlight": (
            theme_def.accent.hex if theme_def.accent else None,
            [theme_def.primary.hex if theme_def.primary else None],
            "#FFFFFF",
        ),
        "danger": (theme_def.error.hex if theme_def.error else None, [], "#FF0000"),
    }

    # Process the mapping to resolve all fallbacks
    theme_styles = {}
    for style_name, (primary, fallbacks, default) in style_mapping.items():
        theme_styles[style_name] = get_fallback_value(primary, fallbacks, default)

    # Create the rich theme and return it
    try:
        return RichTheme(theme_styles)
    except Exception as e:
        logger.error(f"Error creating Rich theme: {e}")
        # Return a basic fallback theme if there's an error
        return RichTheme({"primary": "white", "error": "red"})


def get_gradient_styles(theme_def: ThemeDefinition) -> Dict[str, List[str]]:
    """
    Extract gradient styles from a theme definition with optimized caching.

    This creates a dictionary of gradient styles compatible with
    the gradient_utils module for console rendering.

    Args:
        theme_def: The theme definition to extract gradients from

    Returns:
        Dictionary mapping style names to gradient color lists

    Example:
        >>> theme = get_theme("NEON")
        >>> gradients = get_gradient_styles(theme)
        >>> isinstance(gradients, dict)
        True
        >>> "title" in gradients
        True
    """
    # Use the theme name for the cache key instead of the ThemeDefinition object
    theme_name = theme_def.name

    # Use cache for better performance
    return _gradient_cache.get(theme_name, _compute_gradient_styles, theme_def)


def _compute_gradient_styles(theme_def: ThemeDefinition) -> Dict[str, List[str]]:
    """
    Internal function to compute gradient styles from a theme definition.

    Args:
        theme_def: The theme definition to extract gradients from

    Returns:
        Dictionary of computed gradient styles
    """
    result: Dict[str, Union[str, List[str]]] = {
        "primary": theme_def.primary.hex if theme_def.primary else "#FFFFFF",
        "secondary": (
            theme_def.secondary.hex
            if theme_def.secondary
            else theme_def.primary.hex
            if theme_def.primary
            else "#CCCCCC"
        ),
        "accent": (
            theme_def.accent.hex
            if theme_def.accent
            else theme_def.primary.hex
            if theme_def.primary
            else "#AAAAAA"
        ),
    }

    # Add gradients
    if theme_def.title_gradient:
        result["title"] = theme_def.title_gradient
    elif theme_def.primary and theme_def.primary.gradient:
        result["title"] = theme_def.primary.gradient
    else:
        # Create a simple gradient from the primary color
        hex_color = (theme_def.primary.hex if theme_def.primary else "#FFFFFF").lstrip(
            "#"
        )
        result["title"] = [
            theme_def.primary.hex if theme_def.primary else "#FFFFFF",
            f"#{hex_color}AA",  # 66% opacity
            f"#{hex_color}77",  # 33% opacity
            f"#{hex_color}44",  # 20% opacity
        ]

    # Handle other gradients with similar logic
    if theme_def.artist_gradient:
        result["artist"] = theme_def.artist_gradient
    elif theme_def.secondary and getattr(theme_def.secondary, "gradient", None):
        result["artist"] = theme_def.secondary.gradient
    else:
        hex_color = (
            theme_def.secondary.hex
            if theme_def.secondary
            else theme_def.primary.hex
            if theme_def.primary
            else "#CCCCCC"
        ).lstrip("#")
        result["artist"] = [
            theme_def.secondary.hex
            if theme_def.secondary
            else theme_def.primary.hex
            if theme_def.primary
            else "#CCCCCC",
            f"#{hex_color}AA",
            f"#{hex_color}77",
            f"#{hex_color}44",
        ]

    # Status gradient
    if theme_def.status_gradient:
        result["status"] = theme_def.status_gradient
    else:
        info_color = (
            theme_def.info.hex
            if theme_def.info
            else theme_def.text.hex
            if theme_def.text
            else "#FFFFFF"
        )
        hex_color = info_color.lstrip("#")
        result["status"] = [
            info_color,
            f"#{hex_color}AA",
            f"#{hex_color}77",
        ]

    # Progress gradient
    if theme_def.progress_gradient:
        result["progress"] = theme_def.progress_gradient
    else:
        progress_color = (
            theme_def.success.hex
            if theme_def.success
            else theme_def.accent.hex
            if theme_def.accent
            else theme_def.primary.hex
            if theme_def.primary
            else "#00FF00"
        )
        hex_color = progress_color.lstrip("#")
        result["progress"] = [
            progress_color,
            f"#{hex_color}AA",
        ]

    # Feedback gradient
    if theme_def.feedback_gradient:
        result["feedback"] = theme_def.feedback_gradient
    else:
        feedback_color = (
            theme_def.success.hex
            if theme_def.success
            else theme_def.primary.hex
            if theme_def.primary
            else "#00FF00"
        )
        hex_color = feedback_color.lstrip("#")
        result["feedback"] = [
            feedback_color,
            f"#{hex_color}AA",
            f"#{hex_color}77",
        ]

    # History gradient
    if theme_def.history_gradient:
        result["history"] = theme_def.history_gradient
    else:
        history_color = (
            theme_def.secondary.hex
            if theme_def.secondary
            else theme_def.primary.hex
            if theme_def.primary
            else "#CCCCCC"
        )
        hex_color = history_color.lstrip("#")
        result["history"] = [
            history_color,
            f"#{hex_color}AA",
            f"#{hex_color}77",
            f"#{hex_color}44",
        ]

    # Dim color
    result["dim"] = theme_def.dim if theme_def.dim else "#333333"

    # We know all values in result are either strings or List[str]
    # Cast to the correct return type for type checking
    return cast(Dict[str, List[str]], result)


def invalidate_caches(theme_name: Optional[str] = None) -> None:
    """
    Invalidate the caches for theme conversions.

    Call this function whenever a theme is modified to ensure
    that the cached values are regenerated.

    Args:
        theme_name: Specific theme to invalidate, or None for all themes
    """
    if theme_name:
        _rich_theme_cache.invalidate(theme_name)
        _gradient_cache.invalidate(theme_name)
    else:
        _rich_theme_cache.invalidate()
        _gradient_cache.invalidate()
        # Also clear the lru_cache on the main function
        theme_to_rich_theme.cache_clear()


def create_rich_style_from_color(
    hex_color: str, bold: bool = False, dim: bool = False
) -> Style:
    """
    Create a Rich Style object from a hex color string.

    This is a convenience function for creating a Rich Style object
    with commonly used attributes directly from a hex color.

    Args:
        hex_color: Hex color string
        bold: Whether the style should be bold
        dim: Whether the style should be dim

    Returns:
        A Rich Style object for console styling

    Example:
        >>> style = create_rich_style_from_color("#FF0000", bold=True)
        >>> style.color.name
        '#FF0000'
        >>> style.bold
        True
    """
    try:
        return Style(color=hex_color, bold=bold, dim=dim)
    except Exception as e:
        logger.error(f"Error creating Rich style from color {hex_color}: {e}")
        # Return a default style if there's an error
        return Style(color="white", bold=bold, dim=dim)
