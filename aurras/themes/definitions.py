"""
Theme definitions for the Aurras theme system.

This module defines the core data structures and classes used to represent themes
throughout the application.
"""

from __future__ import annotations

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, TypedDict, Any

from aurras.utils.logger import get_logger
from aurras.themes.colors import ThemeColor

logger = get_logger("aurras.themes.definitions", log_to_console=False)


class ThemeCategory(Enum):
    """Theme categories for organization."""

    DARK = auto()
    LIGHT = auto()
    VIBRANT = auto()
    MINIMAL = auto()
    RETRO = auto()
    NATURAL = auto()
    FUTURISTIC = auto()
    CUSTOM = auto()


class GradientColors(TypedDict, total=False):
    """Typed dictionary for theme gradient colors."""

    title: List[str]
    artist: List[str]
    status: List[str]
    progress: List[str]
    feedback: List[str]
    history: List[str]


class ThemeColorDict(TypedDict, total=False):
    """Typed dictionary for simple color specification."""

    hex: str
    gradient: Optional[List[str]]


@dataclass
class ThemeDefinition:
    """
    Complete theme definition with all color values and metadata.

    This class represents a complete theme definition with all the color values,
    metadata, and gradient values needed to style the application consistently.

    Attributes:
        name: Unique theme identifier (uppercase)
        display_name: User-friendly theme name
        description: Brief description of the theme
        category: Theme category for organization
        dark_mode: Whether this is a dark mode theme
        primary: Primary brand color
        secondary: Secondary color for less emphasis
        accent: Accent color for highlights and focus
        background: Background color for main areas
        surface: Surface color for cards and panels
        panel: Panel background color
        warning: Warning message color
        error: Error message color
        success: Success message color
        info: Informational message color
        text: Main text color
        text_muted: Muted/secondary text color
        border: Border color for UI elements
        title_gradient: Gradient colors for titles
        artist_gradient: Gradient colors for artist names
        status_gradient: Gradient colors for status text
        progress_gradient: Gradient colors for progress bars
        feedback_gradient: Gradient colors for feedback messages
        history_gradient: Gradient colors for history items
        dim: Dim color for de-emphasized UI elements
    """

    # Metadata
    name: str
    display_name: str
    description: str = ""
    category: ThemeCategory = ThemeCategory.CUSTOM
    dark_mode: bool = True

    # Core colors
    primary: Optional[ThemeColor] = None
    secondary: Optional[ThemeColor] = None
    accent: Optional[ThemeColor] = None

    # UI background colors
    background: Optional[ThemeColor] = None
    surface: Optional[ThemeColor] = None
    panel: Optional[ThemeColor] = None

    # Status colors
    warning: Optional[ThemeColor] = None
    error: Optional[ThemeColor] = None
    success: Optional[ThemeColor] = None
    info: Optional[ThemeColor] = None

    # Text colors
    text: Optional[ThemeColor] = None
    text_muted: Optional[ThemeColor] = None
    border: Optional[ThemeColor] = None

    # Gradients
    title_gradient: Optional[List[str]] = None
    artist_gradient: Optional[List[str]] = None
    status_gradient: Optional[List[str]] = None
    progress_gradient: Optional[List[str]] = None
    feedback_gradient: Optional[List[str]] = None
    history_gradient: Optional[List[str]] = None

    # Special fields
    dim: str = "#333333"

    # Custom fields for extensibility
    custom_fields: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate and normalize theme definition."""
        # Ensure name is uppercase for consistency
        self.name = self.name.upper()

        # Normalize and validate field values
        self._normalize_fields()

        # Set default values for any missing required fields
        self._set_defaults()

        # Log validation results
        logger.debug(
            f"Theme '{self.name}' initialized with {self._count_defined_colors()} colors defined"
        )

    def _normalize_fields(self) -> None:
        """Normalize field values, ensuring they have proper types."""
        # Ensure gradient fields are lists of strings
        gradient_fields = [
            "title_gradient",
            "artist_gradient",
            "status_gradient",
            "progress_gradient",
            "feedback_gradient",
            "history_gradient",
        ]

        for field_name in gradient_fields:
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, list):
                try:
                    # If it's not a list but can be converted, do so
                    setattr(self, field_name, list(value))
                    logger.warning(
                        f"Field {field_name} in theme {self.name} was not a list, converted automatically"
                    )
                except (TypeError, ValueError):
                    # If conversion fails, set to None
                    setattr(self, field_name, None)
                    logger.warning(
                        f"Field {field_name} in theme {self.name} had invalid type, set to None"
                    )

    def _set_defaults(self) -> None:
        """Set default values for missing required fields."""
        # Ensure primary color exists
        if not self.primary:
            self.primary = ThemeColor("#FFFFFF")
            logger.warning(
                f"Theme {self.name} missing primary color, using default white"
            )

        # Text color defaults to white for dark themes, black for light themes
        if not self.text:
            self.text = ThemeColor("#FFFFFF" if self.dark_mode else "#000000")

    def _count_defined_colors(self) -> int:
        """Count how many color fields are defined."""
        color_fields = [
            "primary",
            "secondary",
            "accent",
            "background",
            "surface",
            "panel",
            "warning",
            "error",
            "success",
            "info",
            "text",
            "text_muted",
            "border",
        ]

        return sum(1 for field in color_fields if getattr(self, field) is not None)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert theme to a dictionary representation.

        Returns:
            Dictionary with all theme values
        """
        result = {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "category": self.category.name,
            "dark_mode": self.dark_mode,
            "dim": self.dim,
        }

        # Add color fields
        color_fields = [
            "primary",
            "secondary",
            "accent",
            "background",
            "surface",
            "panel",
            "warning",
            "error",
            "success",
            "info",
            "text",
            "text_muted",
            "border",
        ]

        for field in color_fields:
            color_obj = getattr(self, field)
            if color_obj:
                result[field] = color_obj.hex

        # Add gradient fields
        gradient_fields = [
            "title_gradient",
            "artist_gradient",
            "status_gradient",
            "progress_gradient",
            "feedback_gradient",
            "history_gradient",
        ]

        for field in gradient_fields:
            gradient = getattr(self, field)
            if gradient:
                result[field] = gradient

        # Add custom fields
        result.update(self.custom_fields)

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ThemeDefinition:
        """
        Create a ThemeDefinition from a dictionary.

        Args:
            data: Dictionary with theme values

        Returns:
            New ThemeDefinition instance
        """
        # Extract and convert known fields
        theme_data = {}

        # Process required fields
        for field in ["name", "display_name", "description", "dark_mode", "dim"]:
            if field in data:
                theme_data[field] = data[field]

        # Process category field
        if "category" in data:
            category_str = data["category"]
            try:
                theme_data["category"] = (
                    ThemeCategory[category_str]
                    if isinstance(category_str, str)
                    else category_str
                )
            except (KeyError, TypeError):
                logger.warning(f"Invalid category {category_str}, using CUSTOM")
                theme_data["category"] = ThemeCategory.CUSTOM

        # Process color fields
        color_fields = [
            "primary",
            "secondary",
            "accent",
            "background",
            "surface",
            "panel",
            "warning",
            "error",
            "success",
            "info",
            "text",
            "text_muted",
            "border",
        ]

        for field in color_fields:
            if field in data:
                color_value = data[field]
                if isinstance(color_value, str):
                    theme_data[field] = ThemeColor(color_value)
                elif isinstance(color_value, dict) and "hex" in color_value:
                    gradient = color_value.get("gradient")
                    theme_data[field] = ThemeColor(
                        color_value["hex"], gradient=gradient
                    )
                elif hasattr(color_value, "hex"):  # Already a ThemeColor
                    theme_data[field] = color_value

        # Process gradient fields
        gradient_fields = [
            "title_gradient",
            "artist_gradient",
            "status_gradient",
            "progress_gradient",
            "feedback_gradient",
            "history_gradient",
        ]

        for field in gradient_fields:
            if field in data:
                theme_data[field] = data[field]

        # Store any extra fields in custom_fields
        custom_fields = {}
        known_fields = set(theme_data.keys()).union(
            color_fields,
            gradient_fields,
            ["name", "display_name", "description", "category", "dark_mode", "dim"],
        )

        for key, value in data.items():
            if key not in known_fields:
                custom_fields[key] = value

        if custom_fields:
            theme_data["custom_fields"] = custom_fields

        return cls(**theme_data)

    def validate(self) -> List[str]:
        """
        Validate the theme definition.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Check required fields
        if not self.name:
            errors.append("Theme name is required")

        if not self.display_name:
            errors.append("Display name is required")

        # Check that primary color is defined
        if not self.primary:
            errors.append("Primary color is required")

        # Check that text color is defined for usability
        if not self.text:
            errors.append("Text color is required")

        return errors
