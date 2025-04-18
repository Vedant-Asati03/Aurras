"""
Appearance Settings Model

This module defines the Pydantic model for appearance-related settings,
including player visualization, themes, and display preferences.
"""

from pydantic import BaseModel, Field, field_validator

from .validators import validate_theme


class AppearanceSettings(BaseModel):
    # Theme settings
    theme: str = Field(
        default="galaxy",
        title="Theme",
        description="Visual theme for the application",
    )

    # Display settings
    # display_album_art: str = "no"
    display_video: str = "no"
    display_lyrics: str = "yes"
    user_feedback_visible: str = "yes"

    # Format settings
    date_format: str = "yyyy-mm-dd"
    time_format: str = "24h"  # options: 12h, 24h

    model_config = {"extra": "allow"}

    @field_validator("theme", mode="before")
    @classmethod
    def validate_theme_field(cls, v):
        """Validate the theme exists in the available themes."""
        return validate_theme(v)
