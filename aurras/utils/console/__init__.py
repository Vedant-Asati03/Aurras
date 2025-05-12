"""
Console utilities for rich text output and component-based UI.

This package contains utilities for working with Rich console output,
including components, formatters, and renderers.
"""

from aurras.utils.console.manager import get_console, apply_gradient_to_text

console = get_console()

__all__ = [
    "console",
    "apply_gradient_to_text",
]
