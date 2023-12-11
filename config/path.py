from config.config import Config


# cache.db
cache = Config.construct_path("cache.db")
# playlists
saved_playlists = Config.construct_path("playlists.db")
downloaded_playlists = Config.construct_path("playlists")
# spotify_auth.db
spotify_auth = Config.construct_path("spotify_auth.db")
# recommendation.db
recommendation = Config.construct_path("recommendation.db")
# songs
downloaded_songs = Config.construct_path("songs")
# mpv
mpv = Config.construct_path("mpv")
mpv_conf = Config.construct_path(mpv, "mpv.conf")
input_conf = Config.construct_path(mpv, "input.conf")
# logs
aurras_log = Config.construct_path("aurras_app.log")
# settings.yaml
settings = Config.construct_path("settings.yaml")
# user_settings.yaml
custom_settings = Config.construct_path("custom_settings.yaml")
