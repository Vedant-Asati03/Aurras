"""
Path Definition Module

This module defines specific paths used throughout the Aurras application.
It's a compatibility layer that uses PathManager for the actual path construction.
"""

from aurras.utils.path_manager import PathManager

# Create singleton instance
_path_manager = PathManager()

# cache.db
cache = _path_manager.cache_db
# playlists
saved_playlists = _path_manager.saved_playlists
downloaded_playlists = _path_manager.playlists_dir
# spotify_auth.db
spotify_auth = _path_manager.spotify_auth
# recommendation.db
recommendation = _path_manager.recommendation_db
# songs
downloaded_songs = _path_manager.downloaded_songs_dir
# mpv
mpv = _path_manager.mpv_dir
mpv_conf = _path_manager.mpv_conf
input_conf = _path_manager.input_conf
# logs
aurras_log = _path_manager.log_file
# settings.yaml
settings = _path_manager.settings_file
# user_settings.yaml
custom_settings = _path_manager.custom_settings_file
