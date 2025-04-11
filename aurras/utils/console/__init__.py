"""
Console utilities for rich text output and component-based UI.

This package contains utilities for working with Rich console output,
including components, formatters, and renderers.
"""

# Import the main utilities
from .renderer import (
    UIComponent,
    UIRenderer,
    Header,
    ProgressIndicator,
    FeedbackMessage,
    KeybindingHelp,
    get_current_theme_instance,
    get_theme_styles,
    get_theme_gradients,
)

from .formatting import (
    format_time_values,
    format_section_header,
)

from .manager import get_console, get_theme, get_current_theme

__all__ = [
    # UI Components
    "UIComponent",
    "UIRenderer",
    "Header",
    "ProgressIndicator",
    "FeedbackMessage",
    "KeybindingHelp",
    # Theme access functions
    "get_current_theme_instance",
    "get_theme_styles",
    "get_theme_gradients",
    "get_theme",
    "get_current_theme",
    "get_console",
    # Formatting utilities
    "format_time_values",
    "format_section_header",
]
