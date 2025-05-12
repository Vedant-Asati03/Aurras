"""
MPV Player Package

Provides an enhanced MPV player with rich UI, lyrics integration,
and proper integration with the unified database structure.
"""

from aurras.core.player.mpv.core import MPVPlayer
from aurras.core.player.mpv.state import (
    PlaybackState,
    LyricsStatus,
    FeedbackType,
    HistoryCategory,
    Metadata,
    PlayerState,
    UserFeedback,
    HistoryData,
    LyricsState,
)

__all__ = [
    "MPVPlayer",
    "PlaybackState",
    "LyricsStatus",
    "FeedbackType",
    "HistoryCategory",
    "Metadata",
    "PlayerState",
    "UserFeedback",
    "HistoryData",
    "LyricsState",
]
