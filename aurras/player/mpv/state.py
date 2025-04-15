"""
State models for the MPV player.

This module contains all the data models, enums and state classes
used by the MPV player implementation.
"""

from enum import Enum, auto
from dataclasses import dataclass
from concurrent.futures import Future
from typing import Dict, Any, List, Optional, Tuple

ThemeDict = Dict[str, Any]
SongInfo = Tuple[str, str, str]  # song, artist, album


class PlaybackState(Enum):
    """Enum for player playback states."""

    PLAYING = auto()
    PAUSED = auto()
    STOPPED = auto()


class FeedbackType(Enum):
    """Enum for user feedback categories."""

    PLAYBACK = auto()  # Play/pause/stop actions
    NAVIGATION = auto()  # Next/previous/jump tracks
    VOLUME = auto()  # Volume changes
    SEEKING = auto()  # Forward/backward seeking
    THEME = auto()  # Theme changes
    LYRICS = auto()  # Lyrics toggle
    SYSTEM = auto()  # System messages
    ERROR = auto()  # Error messages


class LyricsStatus(Enum):
    """Enum for lyrics availability states."""

    LOADING = auto()  # Lyrics are being fetched
    AVAILABLE = auto()  # Lyrics are available and loaded
    NOT_FOUND = auto()  # No lyrics found for the song
    DISABLED = auto()  # Lyrics feature is disabled


class HistoryCategory(Enum):
    """Enum for categorizing songs based on play count."""

    NEW = 1  # First play
    OCCASIONAL = 2  # Played 2-5 times
    REGULAR = 3  # Played 6-10 times
    FAVORITE = 4  # Played more than 10 times


@dataclass
class Metadata:
    """Data class for song metadata."""

    title: str = "Unknown"
    artist: str = "Unknown"
    album: str = "Unknown"
    duration: float = 0


@dataclass
class PlayerState:
    """Data class for player state information."""

    show_lyrics: bool = True
    playback_state: PlaybackState = PlaybackState.STOPPED
    stop_requested: bool = False
    elapsed_time: float = 0
    current_refresh_rate: float = 0.25
    current_theme: Optional[str] = None
    metadata_ready: bool = False
    current_playlist_pos: int = 0
    queue_start_index: int = 0
    jump_mode: bool = False
    jump_number: str = ""


@dataclass
class UserFeedback:
    """Data class for user action feedback."""

    action: str
    description: str
    feedback_type: FeedbackType
    timestamp: float
    timeout: float = 1.5


@dataclass
class HistoryData:
    """Data class for song history information."""

    play_count: int = 1
    category: HistoryCategory = HistoryCategory.NEW
    last_played: Optional[int] = None
    loaded: bool = False


@dataclass
class LyricsState:
    """Data class for lyrics state."""

    status: LyricsStatus = LyricsStatus.LOADING
    future: Optional[Future] = None
    cached_lyrics: Optional[List[str]] = None
    no_lyrics_message: Optional[str] = None
