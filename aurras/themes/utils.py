"""
Utility functions for the theme system.

This module provides helper functions for working with themes,
including fallback handling and color conversions.
"""

from __future__ import annotations
from typing import Dict, List, Optional, TypeVar, Generic, Callable, overload
import functools
import re

T = TypeVar("T")
V = TypeVar("V")


@overload
def get_fallback_value(
    primary_value: T, fallbacks: List[Optional[T]], default: T
) -> T: ...


@overload
def get_fallback_value(
    primary_value: None, fallbacks: List[Optional[T]], default: T
) -> T: ...


def get_fallback_value(
    primary_value: Optional[T], fallbacks: List[Optional[T]], default: T
) -> T:
    """
    Get a value from a series of fallbacks.

    This function tries a primary value first, then a series of fallbacks,
    and finally returns a default value if all others are None.

    Args:
        primary_value: The primary value to use if not None
        fallbacks: List of fallback values to try in order
        default: Default value to use if all fallbacks are None

    Returns:
        The first non-None value, or the default

    Examples:
        >>> get_fallback_value(None, [None, "fallback"], "default")
        'fallback'
        >>> get_fallback_value("primary", ["fallback"], "default")
        'primary'
        >>> get_fallback_value(None, [None, None], "default")
        'default'
    """
    if primary_value is not None:
        return primary_value

    for fallback in fallbacks:
        if fallback is not None:
            return fallback

    return default


class ThemeValueCache(Generic[T, V]):
    """
    Cache for theme values to avoid expensive recomputation.

    This generic cache can store any type of theme value computation
    with appropriate type safety.

    Type Parameters:
        T: Type of the theme object
        V: Type of the cached values
    """

    def __init__(self, max_size: int = 32):
        """
        Initialize the theme value cache.

        Args:
            max_size: Maximum number of cached values
        """
        self._cache: Dict[str, V] = {}
        self._max_size = max_size

    def get(self, theme_key: str, compute_func: Callable[[T], V], theme_obj: T) -> V:
        """
        Get a cached value or compute it if not cached.

        Args:
            theme_key: Unique key for the theme
            compute_func: Function to compute the value if not cached
            theme_obj: Theme object to pass to compute_func

        Returns:
            Cached or freshly computed value
        """
        if theme_key in self._cache:
            return self._cache[theme_key]

        # Compute new value
        value = compute_func(theme_obj)

        # Cache management: if we're at capacity, remove oldest entry
        if len(self._cache) >= self._max_size:
            # Simple LRU: just remove a random key
            # For true LRU, we'd need more complex tracking
            self._cache.pop(next(iter(self._cache)))

        # Store new value
        self._cache[theme_key] = value

        return value

    def invalidate(self, theme_key: Optional[str] = None) -> None:
        """
        Invalidate cached values.

        Args:
            theme_key: Specific key to invalidate, or None for all
        """
        if theme_key is None:
            self._cache.clear()
        elif theme_key in self._cache:
            del self._cache[theme_key]


def generate_style_mapping(
    theme_values: Dict[str, Optional[str]], fallback_rules: Dict[str, List[str]]
) -> Dict[str, str]:
    """
    Generate a style mapping with fallbacks based on rules.

    This function creates a complete style mapping by applying fallback rules
    to a set of theme values. If a theme value is None, it will use the
    fallback rules to find an alternative.

    Args:
        theme_values: Dictionary of style names to values (can include None)
        fallback_rules: Dictionary of style names to lists of fallback style names

    Returns:
        Complete style mapping with all values resolved

    Examples:
        >>> theme_values = {"primary": "#FF0000", "secondary": None}
        >>> fallback_rules = {"secondary": ["primary"]}
        >>> generate_style_mapping(theme_values, fallback_rules)
        {'primary': '#FF0000', 'secondary': '#FF0000'}
    """
    result = {}

    # First, copy all existing values
    for name, value in theme_values.items():
        if value is not None:
            result[name] = value

    # Then apply fallback rules for missing values
    for name, fallbacks in fallback_rules.items():
        if name not in result:
            # Try each fallback in order
            for fallback in fallbacks:
                if fallback in result:
                    result[name] = result[fallback]
                    break

    return result


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """
    Convert a hex color to RGB values.

    Args:
        hex_color: Hex color string (with or without # prefix)

    Returns:
        Tuple of (r, g, b) values (0-255)

    Raises:
        ValueError: If the hex color is invalid

    Examples:
        >>> hex_to_rgb("#FF0000")
        (255, 0, 0)
        >>> hex_to_rgb("00FF00")
        (0, 255, 0)
    """
    hex_color = hex_color.lstrip("#")

    if len(hex_color) == 3:
        # Convert 3-char hex to 6-char
        hex_color = "".join(c + c for c in hex_color)

    if len(hex_color) != 6:
        raise ValueError(f"Invalid hex color: {hex_color}")

    try:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return (r, g, b)
    except ValueError:
        raise ValueError(f"Invalid hex color: {hex_color}")


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """
    Convert RGB values to a hex color string.

    Args:
        r: Red component (0-255)
        g: Green component (0-255)
        b: Blue component (0-255)

    Returns:
        Hex color string (with # prefix)

    Examples:
        >>> rgb_to_hex(255, 0, 0)
        '#ff0000'
        >>> rgb_to_hex(0, 255, 0)
        '#00ff00'
    """
    return f"#{r:02x}{g:02x}{b:02x}"


def hex_with_alpha(hex_color: str, alpha_percentage: int) -> str:
    """
    Add alpha transparency to a hex color.

    Args:
        hex_color: Hex color string (with or without # prefix)
        alpha_percentage: Alpha percentage (0-100)

    Returns:
        Hex color with alpha component

    Examples:
        >>> hex_with_alpha("#FF0000", 50)
        '#FF000080'
        >>> hex_with_alpha("00FF00", 25)
        '#00FF0040'
    """
    if not 0 <= alpha_percentage <= 100:
        raise ValueError(f"Alpha must be between 0-100, got {alpha_percentage}")

    # Convert percentage to hex (00-FF)
    alpha_hex = int(255 * alpha_percentage / 100)

    # Normalize hex color
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c + c for c in hex_color)

    return f"#{hex_color}{alpha_hex:02x}"


def is_light_color(hex_color: str) -> bool:
    """
    Determine if a color is "light" (should have dark text on it).

    This uses the perceived brightness formula from W3C guidelines.

    Args:
        hex_color: Hex color string

    Returns:
        True if the color is light, False if dark

    Examples:
        >>> is_light_color("#FFFFFF")  # White
        True
        >>> is_light_color("#000000")  # Black
        False
    """
    r, g, b = hex_to_rgb(hex_color)

    # Calculate perceived brightness (W3C formula)
    brightness = (r * 299 + g * 587 + b * 114) / 1000

    # Threshold: 128 is the mid-point, but 150 is often used for better contrast
    return brightness > 150


@functools.lru_cache(maxsize=64)
def validate_hex_color(color: str) -> bool:
    """
    Validate that a string is a proper hex color.

    Args:
        color: String to validate

    Returns:
        True if the string is a valid hex color, False otherwise

    Examples:
        >>> validate_hex_color("#FF0000")
        True
        >>> validate_hex_color("not-a-color")
        False
    """
    # Allow with or without # prefix
    pattern = r"^#?([A-Fa-f0-9]{3}|[A-Fa-f0-9]{6})$"
    return bool(re.match(pattern, color))
