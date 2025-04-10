"""
Console formatting utilities for rich text display.

This module provides utilities for creating visually appealing text formatting
including gradients, color manipulation, and time formatting.
"""

import math
import logging
import colorsys
from typing import List, Tuple

logger = logging.getLogger(__name__)


def _mix_colors(
    color1: Tuple[int, int, int], color2: Tuple[int, int, int], ratio: float
) -> Tuple[int, int, int]:
    """
    Mix two RGB colors with the specified ratio.

    Args:
        color1: First color as (r, g, b) tuple
        color2: Second color as (r, g, b) tuple
        ratio: Mixing ratio (0.0 = all color1, 1.0 = all color2)

    Returns:
        Mixed color as (r, g, b) tuple
    """
    r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
    g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
    b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
    return (r, g, b)


def _get_gradient_colors(theme_key: str = "default") -> List[Tuple[int, int, int]]:
    """
    Get predefined gradient colors based on theme.

    Args:
        theme_key: Identifier for color theme

    Returns:
        List of RGB color tuples for the gradient
    """
    gradient_presets = {
        # Vibrant gradient themes
        "default": [(60, 255, 60), (255, 60, 255)],
        "title": [(60, 255, 255), (255, 60, 255)],  # Cyan to magenta
        "artist": [(255, 140, 0), (255, 0, 128)],  # Orange to pink
        "album": [(70, 130, 180), (100, 149, 237)],  # Steel blue to cornflower blue
        # Monochromatic themes
        "blue": [(30, 60, 255), (30, 200, 255)],  # Deep blue to light blue
        "green": [(0, 100, 0), (0, 255, 127)],  # Dark green to spring green
        "purple": [(75, 0, 130), (238, 130, 238)],  # Indigo to violet
        # Warm themes
        "fire": [(255, 0, 0), (255, 165, 0)],  # Red to orange
        "sunset": [
            (255, 0, 0),
            (255, 165, 0),
            (255, 255, 0),
        ],  # Red to orange to yellow
        # Cool themes
        "ocean": [(0, 0, 139), (0, 191, 255)],  # Dark blue to sky blue
        "forest": [(0, 100, 0), (154, 205, 50)],  # Dark green to yellow-green
        # Neon themes
        "neon": [(255, 0, 255), (0, 255, 255)],  # Magenta to cyan
    }

    return gradient_presets.get(theme_key, gradient_presets["default"])


def apply_gradient_to_text(
    text: str, theme: str = "default", bold: bool = False
) -> str:
    """
    Apply a color gradient to text using Rich markup.

    Args:
        text: The text to apply gradient to
        theme: The gradient theme name
        bold: Whether to make the text bold

    Returns:
        Rich-formatted text with gradient colors applied
    """
    if not text:
        return ""

    # Get gradient colors
    gradient_colors = _get_gradient_colors(theme)

    # Create gradient stops
    num_chars = len(text)

    if num_chars == 0:
        return ""
    elif num_chars == 1:
        color = gradient_colors[0]
        return (
            f"[{'bold ' if bold else ''}rgb({color[0]},{color[1]},{color[2]})]"
            + text
            + "[/]"
        )

    # Create gradient by interpolating between colors
    result = ""
    num_colors = len(gradient_colors)

    for i, char in enumerate(text):
        # Calculate position in gradient
        pos = i / max(1, (num_chars - 1))

        # Find the two colors to interpolate between
        color_idx = min(int(pos * (num_colors - 1)), num_colors - 2)
        color_ratio = (pos * (num_colors - 1)) - color_idx

        # Mix the two colors
        color1 = gradient_colors[color_idx]
        color2 = gradient_colors[color_idx + 1]
        mixed_color = _mix_colors(color1, color2, color_ratio)

        # Add character with color
        result += f"[{'bold ' if bold else ''}rgb({mixed_color[0]},{mixed_color[1]},{mixed_color[2]})]{char}[/]"

    return result


def create_subtle_gradient_text(
    text: str, theme: str = "default", boldness: float = 0.5
) -> str:
    """
    Create a more subtle gradient with less color variation.

    Args:
        text: The text to apply gradient to
        theme: The gradient theme name
        boldness: How bold the gradient should be (0.0 to 1.0)

    Returns:
        Rich-formatted text with subtle gradient applied
    """
    # Get gradient colors and reduce contrast
    gradient_colors = _get_gradient_colors(theme)

    # Create a more muted version for subtle effect
    muted_colors = []

    # Base color (middle of the gradient)
    if len(gradient_colors) == 1:
        base = gradient_colors[0]
    else:
        base = _mix_colors(gradient_colors[0], gradient_colors[-1], 0.5)

    # Create muted version by mixing with base
    for color in gradient_colors:
        muted_colors.append(_mix_colors(base, color, boldness))

    # Apply gradient using muted colors
    num_chars = len(text)

    if num_chars <= 1:
        return (
            text
            if num_chars == 0
            else f"[rgb({muted_colors[0][0]},{muted_colors[0][1]},{muted_colors[0][2]})]"
            + text
            + "[/]"
        )

    # Create gradient
    result = ""
    num_colors = len(muted_colors)

    for i, char in enumerate(text):
        # Calculate position in gradient
        pos = i / (num_chars - 1)

        # Find the two colors to interpolate between
        color_idx = min(int(pos * (num_colors - 1)), num_colors - 2)
        color_ratio = (pos * (num_colors - 1)) - color_idx

        # Mix the two colors
        color1 = muted_colors[color_idx]
        color2 = muted_colors[color_idx + 1]
        mixed_color = _mix_colors(color1, color2, color_ratio)

        # Add character with color
        result += f"[rgb({mixed_color[0]},{mixed_color[1]},{mixed_color[2]})]{char}[/]"

    return result


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


def create_audio_visualization(
    amplitude: float, width: int = 20, height: int = 1
) -> str:
    """
    Create a simple audio visualization based on amplitude.

    Args:
        amplitude: Audio amplitude (0.0 to 1.0)
        width: Width of visualization
        height: Height of visualization in lines

    Returns:
        ASCII/Unicode visualization
    """
    # Normalize amplitude
    amplitude = max(0.0, min(1.0, amplitude))

    # Choose visualization character set based on height
    if height == 1:
        # Single line visualization
        bar_chars = "▁▂▃▄▅▆▇█"
        vis = []

        for i in range(width):
            # Create a wave pattern
            pos = i / width
            # Add some variation by using sine wave
            wave_val = abs(math.sin(pos * math.pi * 2 + (i * 0.2)))
            level = wave_val * amplitude

            # Select character based on level
            char_idx = min(len(bar_chars) - 1, int(level * len(bar_chars)))
            vis.append(bar_chars[char_idx])

        return "".join(vis)
    else:
        # Multi-line visualization (not fully implemented)
        return "▗▄▖\n▐█▌\n▝▀▘" * (width // 3)


def create_rainbow_text(text: str) -> str:
    """
    Create rainbow-colored text.

    Args:
        text: The text to colorize

    Returns:
        Rainbow-colored text in Rich markup
    """
    if not text:
        return ""

    result = ""

    for i, char in enumerate(text):
        # Generate a hue based on position (0.0 to 1.0, wrapping around rainbow)
        hue = (i % 12) / 12.0

        # Convert HSV to RGB (saturation and value at max)
        r, g, b = colorsys.hsv_to_rgb(hue, 0.9, 1.0)

        # Scale to 0-255 range
        r, g, b = int(r * 255), int(g * 255), int(b * 255)

        # Add the character with its color
        result += f"[rgb({r},{g},{b})]{char}[/]"

    return result


def pulse_text(text: str, theme: str = "default", levels: int = 3) -> List[str]:
    """
    Generate pulsing text animation frames.

    Args:
        text: The text to animate
        theme: Color theme to use
        levels: Number of brightness levels

    Returns:
        List of text frames for animation
    """
    gradient_colors = _get_gradient_colors(theme)
    base_color = gradient_colors[0]

    frames = []

    # Create brightness variations
    for i in range(levels):
        # Calculate brightness factor (0.3 to 1.0)
        brightness = 0.3 + (0.7 * (i / (levels - 1)))

        # Adjust color
        r = int(base_color[0] * brightness)
        g = int(base_color[1] * brightness)
        b = int(base_color[2] * brightness)

        # Create frame
        frames.append(f"[rgb({r},{g},{b})]{text}[/]")

    # Add reverse frames for smooth pulsing (except last to avoid duplication)
    frames.extend(frames[-2:0:-1])

    return frames


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
