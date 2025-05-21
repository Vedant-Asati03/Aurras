"""
Shorthand Model

This module defines the Pydantic model for shorthand configuration.
"""

from pydantic import BaseModel


class ShortHandSettings(BaseModel):
    download_song: str = "d"
    play_offline: str = "o"
    play_previous_song: str = "prev"
    play_playlist: str = "p"
    download_playlist: str = "dp"
    view_playlist: str = "v"
    delete_playlist: str = "de"
    display_history: str = "h"

    model_config = {
        # Allow extra fields for backward compatibility
        "extra": "allow"
    }

