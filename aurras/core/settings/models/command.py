"""
Command Model

This module defines the Pydantic model for command configuration.
"""

from pydantic import BaseModel


class CommandSettings(BaseModel):
    download_song: str = "download"
    play_offline: str = "offline"
    play_playlist: str = "playlist"
    download_playlist: str = "downloadp"
    view_playlist: str = "view"
    delete_playlist: str = "delete"
    import_playlist: str = "import"
    search_by_song_or_artist: str = "search"
    display_history: str = "history"
    play_previous_song: str = "previous"
    clear_listening_history: str = "clear"
    setup_spotify: str = "setup"
    display_cache_info: str = "cache"
    cleanup_cache: str = "cleanup"
    toggle_lyrics: str = "lyrics"

    model_config = {
        # Allow extra fields for backward compatibility
        "extra": "allow"
    }
