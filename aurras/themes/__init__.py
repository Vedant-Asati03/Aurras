"""
Aurras unified theme management system.

This package provides a centralized way to define and use themes across both
the console-based (CLI) and text-based user interface (TUI) components of Aurras.
"""

# Core color and definition classes
from .colors import ThemeColor, ColorTriplet
from .definitions import ThemeDefinition, ThemeCategory, GradientColors, ThemeColorDict

# Theme management functions
from .manager import (
    get_theme,
    get_available_themes,
    set_current_theme,
    get_current_theme,
    load_theme_from_file,
    save_theme_to_file,
    discover_user_themes,
    register_user_theme,
    get_themes_by_category,
)

# Theme definitions
from .themes import (
    AVAILABLE_THEMES,
    DEFAULT_THEME,
    # Built-in themes
    GALAXY,
    NEON,
    VINTAGE,
    MINIMAL,
    NIGHTCLUB,
    CYBERPUNK,
    FOREST,
    OCEAN,
    SUNSET,
    MONOCHROME,
)

# Utility functions
from .utils import (
    get_fallback_value,
    generate_style_mapping,
    hex_to_rgb,
    rgb_to_hex,
    hex_with_alpha,
    is_light_color,
    validate_hex_color,
)

# Adapters
from .adapters import (
    theme_to_rich_theme,
    get_gradient_styles,
    theme_to_textual_theme,
    theme_to_text_area_theme,
    theme_to_textual_variables,
)

__all__ = [
    # Core classes
    "ThemeColor",
    "ColorTriplet",
    "ThemeDefinition",
    "ThemeCategory",
    "GradientColors",
    "ThemeColorDict",
    # Management functions
    "get_theme",
    "get_available_themes",
    "set_current_theme",
    "get_current_theme",
    "load_theme_from_file",
    "save_theme_to_file",
    "discover_user_themes",
    "register_user_theme",
    "get_themes_by_category",
    # Theme collections
    "AVAILABLE_THEMES",
    "DEFAULT_THEME",
    # Built-in themes
    "GALAXY",
    "NEON",
    "VINTAGE",
    "MINIMAL",
    "NIGHTCLUB",
    "CYBERPUNK",
    "FOREST",
    "OCEAN",
    "SUNSET",
    "MONOCHROME",
    # Utilities
    "get_fallback_value",
    "generate_style_mapping",
    "hex_to_rgb",
    "rgb_to_hex",
    "hex_with_alpha",
    "is_light_color",
    "validate_hex_color",
    # Adapters
    "theme_to_rich_theme",
    "get_gradient_styles",
    "theme_to_textual_theme",
    "theme_to_text_area_theme",
    "theme_to_textual_variables",
]
