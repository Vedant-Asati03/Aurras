"""
Processors for handling various commands in the AURras application.
"""

from aurras.utils.command.processors.theme import ThemeProcessor
from aurras.utils.command.processors.player import PlayerProcessor
from aurras.utils.command.processors.backup import BackupProcessor
from aurras.utils.command.processors.system import SystemProcessor
from aurras.utils.command.processors.spotify import SpotifyProcessor
from aurras.utils.command.processors.history import HistoryProcessor
from aurras.utils.command.processors.library import LibraryProcessor
from aurras.utils.command.processors.playlist import PlaylistProcessor
from aurras.utils.command.processors.settings import SettingsProcessor

theme_processor = ThemeProcessor()
backup_processor = BackupProcessor()
system_processor = SystemProcessor()
player_processor = PlayerProcessor()
spotify_processor = SpotifyProcessor()
history_processor = HistoryProcessor()
library_processor = LibraryProcessor()
playlist_processor = PlaylistProcessor()
settings_processor = SettingsProcessor()

__all__ = [
    "theme_processor",
    "backup_processor",
    "system_processor",
    "player_processor",
    "spotify_processor",
    "history_processor",
    "library_processor",
    "playlist_processor",
    "settings_processor",
]
