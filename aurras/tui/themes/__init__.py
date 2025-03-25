"""
Theme management for Aurras TUI.
"""

from .theme_manager import (
    Theme,
    TextAreaSettings,
    SyntaxTheme,
    VariableStyles,
    UrlStyles,
    BUILTIN_THEMES,
    load_user_themes,
    load_user_theme,
)

__all__ = [
    "Theme",
    "TextAreaSettings",
    "SyntaxTheme",
    "VariableStyles",
    "UrlStyles",
    "BUILTIN_THEMES",
    "load_user_themes",
    "load_user_theme",
]
