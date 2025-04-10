"""
TUI theme adapter for Aurras.

This module provides integration between the unified theme system
and the Textual-based TUI theme system.
"""

from typing import Dict, Optional, Any, List
import logging
import uuid

from rich.style import Style
from textual.theme import Theme as TextualTheme
from textual.widgets.text_area import TextAreaTheme

from .theme_manager import get_theme, get_current_theme, ThemeDefinition

logger = logging.getLogger(__name__)


def get_fallback_value(
    primary_value: Optional[Any], fallbacks: List[Optional[Any]], default: Any = None
) -> Any:
    """
    Get a value from a series of fallbacks.

    Args:
        primary_value: The primary value to use if not None
        fallbacks: List of fallback values to try
        default: Default value to use if all fallbacks are None

    Returns:
        The first non-None value from the fallbacks, or the default
    """
    if primary_value is not None:
        return primary_value

    for fallback in fallbacks:
        if fallback is not None:
            return fallback

    return default


def generate_style_mapping(theme: ThemeDefinition) -> Dict[str, str]:
    """
    Generate a comprehensive style mapping from a theme.

    This creates a dictionary that maps style names to color values,
    handling fallbacks in a systematic way.

    Args:
        theme: The theme definition to use

    Returns:
        Dictionary mapping style names to color values
    """
    # Define the mapping with fallbacks
    # Format: style_name: (primary_value, [fallback1, fallback2, ...], default)
    style_mapping = {
        # Basic color scheme
        "primary": (theme.primary.hex if theme.primary else None, [], "#FFFFFF"),
        "secondary": (
            theme.secondary.hex if theme.secondary else None,
            [theme.primary.hex if theme.primary else None],
            "#CCCCCC",
        ),
        "accent": (
            theme.accent.hex if theme.accent else None,
            [
                theme.secondary.hex if theme.secondary else None,
                theme.primary.hex if theme.primary else None,
            ],
            "#AAAAAA",
        ),
        # Status colors
        "success": (
            theme.success.hex if theme.success else None,
            [
                theme.accent.hex if theme.accent else None,
                theme.primary.hex if theme.primary else None,
            ],
            "#00FF00",
        ),
        "warning": (theme.warning.hex if theme.warning else None, [], "#FFCC00"),
        "error": (theme.error.hex if theme.error else None, [], "#FF0000"),
        "info": (
            theme.info.hex if theme.info else None,
            [theme.primary.hex if theme.primary else None],
            "#00BFFF",
        ),
        # UI element colors
        "background": (
            theme.background.hex if theme.background else None,
            [],
            "#000000",
        ),
        "surface": (
            theme.surface.hex if theme.surface else None,
            [theme.background.hex if theme.background else None],
            "#333333",
        ),
        "panel": (
            theme.panel.hex if theme.panel else None,
            [
                theme.surface.hex if theme.surface else None,
                theme.background.hex if theme.background else None,
            ],
            "#444444",
        ),
        # Text colors
        "text": (theme.text.hex if theme.text else None, [], "#FFFFFF"),
        "text-muted": (
            theme.text_muted.hex if theme.text_muted else None,
            [theme.text.hex if theme.text else None],
            "#CCCCCC",
        ),
        # Playback UI element styles
        "title": (
            f"bold {theme.primary.hex}" if theme.primary else None,
            [],
            "bold white",
        ),
        "artist": (
            theme.secondary.hex if theme.secondary else None,
            [theme.primary.hex if theme.primary else None],
            "#DDDDDD",
        ),
        "album": (
            theme.accent.hex if theme.accent else None,
            [
                theme.secondary.hex if theme.secondary else None,
                theme.primary.hex if theme.primary else None,
            ],
            "#BBBBBB",
        ),
        "controls": (
            theme.accent.hex if theme.accent else None,
            [theme.primary.hex if theme.primary else None],
            "#FFFFFF",
        ),
        "playing": (
            f"bold {theme.success.hex}" if theme.success else None,
            [f"bold {theme.primary.hex}" if theme.primary else None],
            "bold green",
        ),
        "duration": (
            theme.text.hex if theme.text else None,
            [theme.text_muted.hex if theme.text_muted else None],
            "#FFFFFF",
        ),
        # Input and interaction styles
        "input-cursor-background": (
            theme.primary.hex if theme.primary else None,
            [],
            "#FFFFFF",
        ),
        "input-selection-background": (
            f"{theme.primary.hex} 35%" if theme.primary else None,
            [],
            "#FFFFFF 35%",
        ),
        "border-color": (
            theme.border.hex if theme.border else None,
            [f"{theme.primary.hex} 30%" if theme.primary else None],
            "#555555",
        ),
        "selection": (
            f"{theme.primary.hex} 30%" if theme.primary else None,
            [],
            "#FFFFFF 30%",
        ),
    }

    # Process the mapping to resolve all fallbacks
    resolved_mapping = {}
    for style_name, (primary, fallbacks, default) in style_mapping.items():
        resolved_mapping[style_name] = get_fallback_value(primary, fallbacks, default)

    return resolved_mapping


def unified_to_textual_theme(theme_def: ThemeDefinition) -> TextualTheme:
    """
    Convert a unified theme definition to a Textual Theme.

    Args:
        theme_def: The unified theme definition to convert

    Returns:
        The converted Textual theme
    """
    # Extract basic theme args
    theme_args = {
        "name": theme_def.display_name.lower().replace(" ", "_"),
        "primary": theme_def.primary.hex,
        "dark": theme_def.dark_mode,
    }

    # Add optional colors using our new helper
    style_mapping = generate_style_mapping(theme_def)

    # Add optional color fields
    color_fields = {
        "secondary": "secondary",
        "background": "background",
        "surface": "surface",
        "panel": "panel",
        "warning": "warning",
        "error": "error",
        "success": "success",
        "accent": "accent",
    }

    for theme_arg, style_name in color_fields.items():
        if style_name in style_mapping:
            theme_args[theme_arg] = style_mapping[style_name]

    # Get theme variables from the style mapping
    variables = {}
    for style_name, value in style_mapping.items():
        if style_name not in color_fields.values() and "-" in style_name:
            # This is a variable name (like input-cursor-background)
            variables[style_name] = value

    # Add common variables
    if "text" in style_mapping:
        variables["text"] = style_mapping["text"]
    if "text-muted" in style_mapping:
        variables["text-muted"] = style_mapping["text-muted"]

    # Generate primary color shades
    variables["primary-darken-1"] = theme_def.primary.darken(0.1)
    variables["primary-darken-2"] = theme_def.primary.darken(0.2)

    # Add footer styling
    variables["footer-background"] = "transparent"

    # Check if we have enough settings to add theme variables
    if variables:
        theme_args["variables"] = variables

    return TextualTheme(**theme_args)


def get_textual_theme(theme_name: Optional[str] = None) -> TextualTheme:
    """
    Get a Textual theme from the unified theme system.

    Args:
        theme_name: Optional name of the theme to get, or None for current theme

    Returns:
        A Textual theme instance

    Raises:
        KeyError: If the requested theme does not exist
    """
    if theme_name is None:
        theme_name = get_current_theme()

    # Get the theme from the unified system
    theme_def = get_theme(theme_name)

    # Convert to Textual theme
    return unified_to_textual_theme(theme_def)


def get_available_textual_themes() -> Dict[str, TextualTheme]:
    """
    Get all available themes as Textual themes.

    Returns:
        Dictionary of theme names to Textual themes
    """
    from .theme_manager import AVAILABLE_THEMES

    return {
        name.lower(): unified_to_textual_theme(theme_def)
        for name, theme_def in AVAILABLE_THEMES.items()
    }


def get_text_area_theme(theme_name: Optional[str] = None) -> TextAreaTheme:
    """
    Create a TextAreaTheme from the unified theme system.

    Args:
        theme_name: Optional name of the theme to use, or None for current theme

    Returns:
        A TextAreaTheme instance compatible with Textual text areas
    """
    if theme_name is None:
        theme_name = get_current_theme()

    # Get the theme from the unified system
    theme_def = get_theme(theme_name)

    # Generate style mapping
    style_mapping = generate_style_mapping(theme_def)

    # Define text area specific variables
    text_area_vars = {
        "gutter": style_mapping.get("text-muted", "#CCCCCC"),
        "cursor": style_mapping.get("primary", "#FFFFFF"),
        "cursor-line": f"{style_mapping.get('primary', '#FFFFFF')} 10%",
        "cursor-line-gutter": style_mapping.get("surface", "#333333"),
        "matched-bracket": style_mapping.get("accent", "#AAAAAA"),
        "selection": f"{style_mapping.get('primary', '#FFFFFF')} 30%",
    }

    # Create syntax highlighting styles
    syntax_styles = {
        "json-key": Style.parse(style_mapping.get("primary", "#FFFFFF")),
        "json-string": Style.parse(style_mapping.get("success", "#00FF00")),
        "json-number": Style.parse(style_mapping.get("warning", "#FFCC00")),
        "json-boolean": Style.parse(style_mapping.get("error", "#FF0000")),
        "json-null": Style.parse(style_mapping.get("text-muted", "#CCCCCC")),
    }

    # Create the TextAreaTheme
    return TextAreaTheme(
        name=f"{theme_def.name.lower()}_text_area_{uuid.uuid4().hex[:8]}",
        syntax_styles=syntax_styles,
        gutter_style=Style.parse(text_area_vars["gutter"]),
        cursor_style=Style.parse(text_area_vars["cursor"]),
        cursor_line_style=Style.parse(text_area_vars["cursor-line"]),
        cursor_line_gutter_style=Style.parse(text_area_vars["cursor-line-gutter"]),
        bracket_matching_style=Style.parse(text_area_vars["matched-bracket"]),
        selection_style=Style.parse(text_area_vars["selection"]),
    )
