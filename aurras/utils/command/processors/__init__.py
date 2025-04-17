"""
Processors for handling various commands in the AURras application.
"""

from .theme import ThemeProcessor
from .player import PlayerProcessor
from .backup import BackupProcessor
from .history import HistoryProcessor
from .library import LibraryProcessor
from .playlist import PlaylistProcessor
from .settings import SettingsProcessor

__all__ = [
    "PlayerProcessor",
    "PlaylistProcessor",
    "HistoryProcessor",
    "LibraryProcessor",
    "ThemeProcessor",
    "SettingsProcessor",
    "BackupProcessor",
]
