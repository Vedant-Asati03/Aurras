"""
Console formatting utilities for rich text display.

This module provides utilities for formatting text and values
for display in the terminal, such as time formatting.
"""

from aurras.utils.logger import get_logger

logger = get_logger("aurras.utils.console.formatting", log_to_console=False)


def format_time_values(seconds: float) -> str:
    """
    Format time in seconds to a human-readable format.

    Args:
        seconds: Time in seconds

    Returns:
        Formatted time string (MM:SS or HH:MM:SS)
    """
    seconds = max(0, seconds)

    # Round to nearest second
    seconds = round(seconds)

    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60

    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"


def format_section_header(text: str, style: str = "cyan") -> str:
    """
    Format section headers with consistent styling.

    Args:
        text: Header text
        style: Color style to apply

    Returns:
        Formatted section header
    """
    # Create a decorative header with consistent styling
    line_char = "═"
    line_width = 50

    # Create the top decorative line
    top_line = f"[dim {style}]{line_char * ((line_width - len(text) - 4) // 2)}[/]"
    bottom_line = f"[dim {style}]{line_char * line_width}[/]"

    # Create the formatted header with decorations
    formatted_header = f"{top_line} [bold {style}]{text}[/] {top_line}\n"

    return formatted_header
