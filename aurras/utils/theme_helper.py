"""
Common utilities for command processors.

This module contains shared functionality used across different command processors,
such as theme handling and error management.
"""

import logging
from functools import wraps
from typing import Any, Dict

from .console.manager import get_console
from .console.renderer import (
    get_current_theme_instance,
    get_theme_styles,
)

console = get_console()
logger = logging.getLogger(__name__)


class ThemeHelper:
    """Helper class for theme operations to reduce code duplication."""

    @staticmethod
    def get_theme_colors() -> Dict[str, Any]:
        """Get theme colors for consistent styling."""
        theme_obj = get_current_theme_instance()
        theme_styles = get_theme_styles(theme_obj)
        return theme_styles

    @staticmethod
    def get_styled_text(
        text: str, style_key: str = "primary", bold: bool = False
    ) -> str:
        """Format text with theme-consistent styling."""
        theme_styles = ThemeHelper.get_theme_colors()
        color = theme_styles.get(style_key, "blue")
        bold_prefix = "bold " if bold else ""
        return f"[{bold_prefix}{color}]{text}[/{bold_prefix}{color}]"

    @staticmethod
    def format_message(message: str, style_key: str = "primary") -> str:
        """Format a message with theme-consistent styling."""
        theme_styles = ThemeHelper.get_theme_colors()
        color = theme_styles.get(style_key, "blue")
        return f"[{color}]{message}[/{color}]"

    @staticmethod
    def get_theme_color(key: str, default: str = "#FFFFFF") -> str:
        """
        Get a theme color with fallback.

        Args:
            key: The theme color key
            default: Default color if key not found

        Returns:
            Color value suitable for Rich styling
        """
        theme_obj = get_current_theme_instance()
        theme_styles = get_theme_styles(theme_obj)

        style = theme_styles.get(key)
        if isinstance(style, str):
            return style
        elif hasattr(style, "color") and style.color:
            return style.color.name if hasattr(style.color, "name") else default
        else:
            return default


def with_error_handling(method):
    """Decorator to standardize error handling in processor methods."""

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except Exception as e:
            theme_styles = ThemeHelper.get_theme_colors()
            error_color = theme_styles.get("error", "red")
            method_name = method.__name__
            console.print(
                f"[{error_color}]Error in {method_name}:[/{error_color}] {str(e)}"
            )
            logger.error(f"Error in {method_name}: {e}", exc_info=True)
            return 1

    return wrapper
