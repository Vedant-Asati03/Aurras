"""
Keyboard Shortcuts Model

This module defines the Pydantic model for keyboard shortcuts configuration.
"""

from pydantic import BaseModel


class KeyboardShortcuts(BaseModel):
    quit_playback: str = "q"
    toggle_play_pause: str = "SPACE"
    next_track: str = "n"
    previous_track: str = "b"
    toggle_shuffle: str = "s"
    toggle_repeat: str = "r"
    volume_up: str = "UP"
    volume_down: str = "DOWN"
    toggle_mute: str = "m"
    seek_forward: str = "RIGHT"
    seek_backward: str = "LEFT"
    toggle_lyrics: str = "l"
    stop_jump_mode: str = "ESC"
    switch_themes: str = "t"

    model_config = {
        # Allow extra fields for backward compatibility
        "extra": "allow"
    }
