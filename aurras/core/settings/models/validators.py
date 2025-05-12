"""
Settings Validators

This module provides validation functions for settings values.
"""

from typing import List

# We'll define this later to avoid circular imports
AVAILABLE_THEMES: List[str] = []


def validate_volume(v):
    """
    Ensure volume is between 0 and 200.

    Args:
        v: The volume value to validate

    Returns:
        Validated volume as a string
    """
    try:
        vol = int(v)
        if vol < 0 or vol > 200:
            return "100"  # Default if out of range
        return str(vol)
    except (ValueError, TypeError):
        return "100"  # Default if conversion fails


def validate_theme(v):
    """
    Validate that the theme is one of the supported options.

    Args:
        v: The theme value to validate

    Returns:
        Validated theme name
    """
    if not isinstance(v, str):
        return "galaxy"  # Default theme

    theme = v.lower().strip(" ")

    # Import here to avoid circular imports
    try:
        from aurras.themes.manager import get_available_themes

        # Populate the global AVAILABLE_THEMES list
        global AVAILABLE_THEMES
        if not AVAILABLE_THEMES:
            AVAILABLE_THEMES = [t.lower() for t in get_available_themes()]
    except ImportError:
        # If we can't import (during initialization), use a fallback
        if not AVAILABLE_THEMES:
            AVAILABLE_THEMES = [
                "galaxy",
                "neon",
                "vintage",
                "minimal",
                "nightclub",
                "cyberpunk",
                "forest",
                "ocean",
                "sunset",
                "monochrome",
            ]

    if theme not in AVAILABLE_THEMES:
        return "galaxy"  # Default to galaxy if invalid

    return theme
