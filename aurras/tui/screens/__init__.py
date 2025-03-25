"""
TUI screens for the Aurras Music Player.
"""

from .home import HomeScreen
from .playlist import PlaylistScreen
from .lyrics import LyricsScreen
from .downloads import DownloadsScreen
from .settings import SettingsScreen

__all__ = [
    "HomeScreen",
    "PlaylistScreen",
    "LyricsScreen",
    "DownloadsScreen",
    "SettingsScreen",
]
