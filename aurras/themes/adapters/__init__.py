"""
Theme adapters for converting themes to different output formats.

This package provides adapters to convert themes between formats
for different UI frameworks used in Aurras.
"""

from .rich_adapter import (
    theme_to_rich_theme,
    get_gradient_styles,
    invalidate_caches,
    create_rich_style_from_color,
)

from .textual_adapter import (
    theme_to_textual_theme,
    theme_to_text_area_theme,
    theme_to_textual_variables,
)

__all__ = [
    # Rich adapter
    "theme_to_rich_theme",
    "get_gradient_styles",
    "invalidate_caches",
    "create_rich_style_from_color",
    # Textual adapter
    "theme_to_textual_theme",
    "theme_to_text_area_theme",
    "theme_to_textual_variables",
]
