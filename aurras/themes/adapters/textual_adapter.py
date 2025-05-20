"""
Textual adapter for the Aurras theme system.

This module provides functionality to convert theme definitions
to Textual library compatible formats for the TUI interface.
"""

import uuid
from typing import Dict

from rich.style import Style
from textual.theme import Theme as TextualTheme
from textual.widgets.text_area import TextAreaTheme

from aurras.utils.logger import get_logger
from aurras.themes.utils import get_fallback_value
from aurras.themes.definitions import ThemeDefinition

logger = get_logger("aurras.themes.adapters.textual_adapter", log_to_console=False)


def theme_to_textual_theme(theme_def: ThemeDefinition) -> TextualTheme:
    """
    Convert a ThemeDefinition to a Textual Theme.

    Args:
        theme_def: The theme definition to convert

    Returns:
        A Textual Theme instance for TUI rendering
    """
    # Extract basic theme args
    theme_args = {
        "name": theme_def.display_name.lower().replace(" ", "_"),
        "primary": theme_def.primary.hex if theme_def.primary else "#FFFFFF",
        "dark": theme_def.dark_mode,
    }

    # Define style mappings with fallbacks
    style_mapping = {
        # Basic color scheme
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
        # UI element colors
        "background": (
            theme_def.background.hex if theme_def.background else None,
            [],
            "#000000",
        ),
        "surface": (
            theme_def.surface.hex if theme_def.surface else None,
            [theme_def.background.hex if theme_def.background else None],
            "#333333",
        ),
        "panel": (
            theme_def.panel.hex if theme_def.panel else None,
            [
                theme_def.surface.hex if theme_def.surface else None,
                theme_def.background.hex if theme_def.background else None,
            ],
            "#444444",
        ),
        # Text colors
        "text": (theme_def.text.hex if theme_def.text else None, [], "#FFFFFF"),
        "text-muted": (
            theme_def.text_muted.hex if theme_def.text_muted else None,
            [theme_def.text.hex if theme_def.text else None],
            "#CCCCCC",
        ),
        # Input and interaction styles
        "input-cursor-background": (
            theme_def.primary.hex if theme_def.primary else None,
            [],
            "#FFFFFF",
        ),
        "input-selection-background": (
            f"{theme_def.primary.hex} 35%" if theme_def.primary else None,
            [],
            "#FFFFFF 35%",
        ),
        "footer-background": (None, [], "transparent"),
        "border-color": (
            theme_def.border.hex if theme_def.border else None,
            [f"{theme_def.primary.hex} 30%" if theme_def.primary else None],
            "#555555",
        ),
        "selection": (
            f"{theme_def.primary.hex} 30%" if theme_def.primary else None,
            [],
            "#FFFFFF 30%",
        ),
    }

    # Add optional color fields to theme args
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

    # Process the mapping to resolve all fallbacks
    variables = {}
    for style_name, (primary, fallbacks, default) in style_mapping.items():
        value = get_fallback_value(primary, fallbacks, default)

        # Add to theme args if it's a main color
        if style_name in color_fields:
            theme_args[style_name] = value
        # Otherwise add to variables
        elif "-" in style_name:
            variables[style_name] = value

    # Add text colors to variables
    if "text" in style_mapping:
        variables["text"] = get_fallback_value(
            style_mapping["text"][0], style_mapping["text"][1], style_mapping["text"][2]
        )

    if "text-muted" in style_mapping:
        variables["text-muted"] = get_fallback_value(
            style_mapping["text-muted"][0],
            style_mapping["text-muted"][1],
            style_mapping["text-muted"][2],
        )

    # Generate primary color shades
    variables["primary-darken-1"] = (
        theme_def.primary.darken(0.1) if theme_def.primary else "#DDDDDD"
    )
    variables["primary-darken-2"] = (
        theme_def.primary.darken(0.2) if theme_def.primary else "#BBBBBB"
    )

    # Add variables to theme args if we have any
    if variables:
        theme_args["variables"] = variables

    return TextualTheme(**theme_args)


def theme_to_text_area_theme(theme_def: ThemeDefinition) -> TextAreaTheme:
    """
    Create a TextAreaTheme from a ThemeDefinition.

    Args:
        theme_def: The theme definition to convert

    Returns:
        A TextAreaTheme instance for code editors
    """
    # First get the basic theme variables
    textual_theme = theme_to_textual_theme(theme_def)
    variables = textual_theme.variables if hasattr(textual_theme, "variables") else {}

    # Define text area specific variables with fallbacks
    text_area_vars = {
        "gutter": get_fallback_value(
            variables.get("text-muted"), [variables.get("text")], "#CCCCCC"
        ),
        "cursor": get_fallback_value(
            variables.get("input-cursor-background"),
            [variables.get("primary")],
            "#FFFFFF",
        ),
        "cursor-line": f"{variables.get('primary', '#FFFFFF')} 10%",
        "cursor-line-gutter": get_fallback_value(
            variables.get("surface"), [variables.get("background")], "#333333"
        ),
        "matched-bracket": get_fallback_value(
            variables.get("accent"), [variables.get("primary")], "#AAAAAA"
        ),
        "selection": get_fallback_value(
            variables.get("selection"),
            [f"{variables.get('primary', '#FFFFFF')} 30%"],
            "#FFFFFF 30%",
        ),
    }

    # Define syntax highlighting styles
    primary = variables.get("primary", "#FFFFFF")
    success = variables.get("success", "#00FF00")
    warning = variables.get("warning", "#FFCC00")
    error = variables.get("error", "#FF0000")
    text_muted = variables.get("text-muted", "#CCCCCC")

    syntax_styles = {
        "json-key": Style.parse(primary),
        "json-string": Style.parse(success),
        "json-number": Style.parse(warning),
        "json-boolean": Style.parse(error),
        "json-null": Style.parse(text_muted),
    }

    # Create the TextAreaTheme
    theme_name = f"{theme_def.name.lower()}_text_area_{uuid.uuid4().hex[:8]}"

    return TextAreaTheme(
        name=theme_name,
        syntax_styles=syntax_styles,
        gutter_style=Style.parse(text_area_vars["gutter"]),
        cursor_style=Style.parse(text_area_vars["cursor"]),
        cursor_line_style=Style.parse(text_area_vars["cursor-line"]),
        cursor_line_gutter_style=Style.parse(text_area_vars["cursor-line-gutter"]),
        bracket_matching_style=Style.parse(text_area_vars["matched-bracket"]),
        selection_style=Style.parse(text_area_vars["selection"]),
    )


def theme_to_textual_variables(theme_def: ThemeDefinition) -> Dict[str, str]:
    """
    Convert a ThemeDefinition to Textual theme variables.

    This can be used to extend an existing Textual theme with
    variables from an Aurras theme.

    Args:
        theme_def: The theme definition to convert

    Returns:
        Dictionary of CSS variables for Textual
    """
    # Create a Textual theme first
    textual_theme = theme_to_textual_theme(theme_def)

    # Extract and return the variables
    return textual_theme.variables if hasattr(textual_theme, "variables") else {}
