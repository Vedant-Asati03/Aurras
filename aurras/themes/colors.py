"""
Color management for the Aurras theme system.

This module provides classes and utilities for working with colors
in a consistent way across the application.
"""

from __future__ import annotations

import re
import colorsys

from typing import List, Optional, cast
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ColorTriplet:
    """
    RGB color triplet with integer components (0-255).

    Attributes:
        red: Red component (0-255)
        green: Green component (0-255)
        blue: Blue component (0-255)
    """

    red: int
    green: int
    blue: int

    def __post_init__(self) -> None:
        """Validate color components."""
        for attr, value in [
            ("red", self.red),
            ("green", self.green),
            ("blue", self.blue),
        ]:
            if not isinstance(value, int) or not (0 <= value <= 255):
                raise ValueError(f"{attr} must be an integer between 0-255")

    def to_hex(self) -> str:
        """Convert to hex string without # prefix."""
        return f"{self.red:02x}{self.green:02x}{self.blue:02x}"

    @classmethod
    def from_hex(cls, hex_str: str) -> "ColorTriplet":
        """Create from hex string."""
        hex_str = hex_str.lstrip("#")
        if len(hex_str) == 3:
            hex_str = "".join(c + c for c in hex_str)
        if len(hex_str) != 6:
            raise ValueError(f"Invalid hex color: {hex_str}")
        try:
            r = int(hex_str[0:2], 16)
            g = int(hex_str[2:4], 16)
            b = int(hex_str[4:6], 16)
            return cls(red=r, green=g, blue=b)
        except ValueError:
            raise ValueError(f"Invalid hex color: {hex_str}")


@dataclass(frozen=True)
class ThemeColor:
    """
    A color definition with support for hex values, gradients, and transformations.

    This class represents a color in the theme system and provides methods
    for manipulating and transforming the color for different contexts.

    Attributes:
        hex: The hexadecimal color value (e.g., "#FF5733")
        gradient: Optional list of colors forming a gradient
        triplet: Optional color triplet for faster color operations

    Examples:
        >>> primary = ThemeColor("#FF5733")
        >>> primary.with_alpha(50)
        '#FF5733 50%'
        >>> primary.darken(0.2)
        '#CC451F'
    """

    hex: str
    gradient: Optional[List[str]] = field(default=None)
    triplet: Optional[ColorTriplet] = field(default=None, repr=False)

    def __post_init__(self) -> None:
        """Validate the hex color value and normalize it."""
        # Validate hex color format using a simple check
        hex_value = self.hex.lstrip("#")
        if not re.match(r"^[0-9A-Fa-f]{3}([0-9A-Fa-f]{3})?$", hex_value):
            raise ValueError(f"Invalid hex color: {self.hex}")

        # Ensure the hex value includes the # prefix
        if not self.hex.startswith("#"):
            object.__setattr__(self, "hex", f"#{self.hex}")

        # Create triplet if not provided
        if self.triplet is None:
            object.__setattr__(self, "triplet", ColorTriplet.from_hex(hex_value))

    @property
    def rich_color(self) -> str:
        """Return the color value formatted for Rich library."""
        return self.hex

    def with_alpha(self, alpha_percentage: int) -> str:
        """
        Return the color with the specified alpha value.

        Args:
            alpha_percentage: Alpha value, 0-100 (0 = transparent, 100 = opaque)

        Returns:
            String representation with alpha for use in UI frameworks

        Raises:
            ValueError: If alpha_percentage is outside the valid range
        """
        if not 0 <= alpha_percentage <= 100:
            raise ValueError(f"Alpha must be between 0-100, got {alpha_percentage}")
        return f"{self.hex} {alpha_percentage}%"

    def darken(self, amount: float = 0.1) -> str:
        """
        Return a darkened version of this color.

        Args:
            amount: Amount to darken (0.0-1.0)

        Returns:
            Hex color string of the darkened color
        """
        if not 0 <= amount <= 1:
            raise ValueError(f"Darken amount must be between 0-1, got {amount}")

        triplet = cast(
            ColorTriplet, self.triplet
        )  # We know it's not None after post_init
        r, g, b = triplet.red / 255.0, triplet.green / 255.0, triplet.blue / 255.0

        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        v = max(0, v - amount)  # Reduce value to darken
        r, g, b = colorsys.hsv_to_rgb(h, s, v)

        return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"

    def lighten(self, amount: float = 0.1) -> str:
        """
        Return a lightened version of this color.

        Args:
            amount: Amount to lighten (0.0-1.0)

        Returns:
            Hex color string of the lightened color
        """
        if not 0 <= amount <= 1:
            raise ValueError(f"Lighten amount must be between 0-1, got {amount}")

        triplet = cast(
            ColorTriplet, self.triplet
        )  # We know it's not None after post_init
        r, g, b = triplet.red / 255.0, triplet.green / 255.0, triplet.blue / 255.0

        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        v = min(1, v + amount)  # Increase value to lighten
        r, g, b = colorsys.hsv_to_rgb(h, s, v)

        return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"

    @classmethod
    def from_rgb(cls, r: int, g: int, b: int) -> "ThemeColor":
        """
        Create a ThemeColor from RGB values.

        Args:
            r: Red component (0-255)
            g: Green component (0-255)
            b: Blue component (0-255)

        Returns:
            New ThemeColor instance
        """
        triplet = ColorTriplet(red=r, green=g, blue=b)
        hex_value = f"#{triplet.to_hex()}"
        return cls(hex=hex_value, triplet=triplet)

    @classmethod
    def from_hsv(cls, h: float, s: float, v: float) -> "ThemeColor":
        """
        Create a ThemeColor from HSV values.

        Args:
            h: Hue (0.0-1.0)
            s: Saturation (0.0-1.0)
            v: Value (0.0-1.0)

        Returns:
            New ThemeColor instance
        """
        if not all(0 <= val <= 1 for val in (h, s, v)):
            raise ValueError("HSV values must be between 0-1")

        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return cls.from_rgb(int(r * 255), int(g * 255), int(b * 255))

    def generate_gradient(self, steps: int = 4) -> List[str]:
        """
        Generate a gradient from this color to white or black.

        Args:
            steps: Number of gradient steps to generate

        Returns:
            List of hex color strings in the gradient
        """
        if steps < 2:
            return [self.hex]

        triplet = cast(
            ColorTriplet, self.triplet
        )  # We know it's not None after post_init
        r, g, b = triplet.red / 255.0, triplet.green / 255.0, triplet.blue / 255.0

        # Determine if the color is light or dark to create contrasting gradient
        brightness = 0.299 * r + 0.587 * g + 0.114 * b
        is_light = brightness > 0.5

        h, s, v = colorsys.rgb_to_hsv(r, g, b)

        result = [self.hex]

        for i in range(1, steps):
            # For dark colors, increase value; for light colors, reduce value
            if is_light:
                new_v = max(0, v - (v * (i / steps)))
                new_s = min(1, s + ((1 - s) * (i / steps)))
            else:
                new_v = min(1, v + ((1 - v) * (i / steps)))
                new_s = max(0, s - (s * (i / steps)))

            new_r, new_g, new_b = colorsys.hsv_to_rgb(h, new_s, new_v)
            hex_color = (
                f"#{int(new_r * 255):02x}{int(new_g * 255):02x}{int(new_b * 255):02x}"
            )
            result.append(hex_color)

        return result
