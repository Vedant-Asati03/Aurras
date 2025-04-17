"""
Completer Module

This module provides a registry for prompt_toolkit completers based on input patterns.
"""

from .base import BaseCompleter
from .song import SongCompleter
from .command import CommandCompleter
from .feature import FeatureCompleter
from .history import SongHistoryManager
from .playlist import PlaylistCompleter


__all__ = [
    "BaseCompleter",
    "SongCompleter",
    "CommandCompleter",
    "FeatureCompleter",
    "SongHistoryManager",
    "PlaylistCompleter",
]
