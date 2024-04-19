from rich.text import Text
from rich.console import Console
import questionary

from config import path
from config.settings.create_default_settings import CreateDefaultSettings
from src.scripts.downloadsong import SongDownloader
from src.command_palette.command_palette_config import DisplaySettings
from src.scripts.playlist.delete_playlist import DeletePlaylist
from src.scripts.playlist.download_playlist import DownloadPlaylist
from src.scripts.playsong.listen_online import ListenSongOnline, ListenPlaylistOnline
from src.scripts.playsong.listen_offline import ListenSongOffline, ListenPlaylistOffline
from src.scripts.playlist.import_playlist.import_from_spotify import (
    ImportSpotifyPlaylist,
)


class InputCases:
    def __init__(self) -> None:
        self.console = Console()

    def play_offline(self):
        ListenSongOffline().listen_song_offline()

    def download_song(self, songs_to_download=None):
        if songs_to_download == []:
            songs_to_download = self.console.input(
                Text("Enter song name[s]: ", style="#A2DE96")
            ).split(",")

        download = SongDownloader(songs_to_download, path.downloaded_songs)
        download.download_song()

    def play_playlist(self, online_offline=None, playlist_name=None):
        listen_playlist_online = ListenPlaylistOnline()
        listen_playlist_offline = ListenPlaylistOffline()

        if online_offline is None:
            online_offline = questionary.select(
                "", choices=["Play Online", "Play Offline"]
            ).ask()

            online_offline = "n" if online_offline == "Play Online" else "f"

        match online_offline:
            case "n":
                listen_playlist_online.listen_playlist_online(playlist_name)
            case "f":
                listen_playlist_offline.listen_playlist_offline(playlist_name)

    def delete_playlist(self, saved_downloaded=None, playlist_name=""):
        delete_playlist = DeletePlaylist()

        if saved_downloaded is None:
            saved_downloaded = questionary.select(
                "Select Playlist to Delete",
                choices=["Saved Playlists", "Downloaded Playlists"],
            ).ask()

            saved_downloaded = "s" if saved_downloaded == "Saved Playlists" else "d"

        match saved_downloaded:
            case "s":
                delete_playlist.delete_saved_playlist(playlist_name)
            case "d":
                print(playlist_name)
                delete_playlist.delete_downloaded_playlist(playlist_name)

    def import_playlist(self):
        ImportSpotifyPlaylist().import_spotify_playlist()

    def download_playlist(self, playlist_name=None):
        DownloadPlaylist().download_playlist(playlist_name)

    def settings(self):
        DisplaySettings().display_settings()

    def reset_setting(self):
        CreateDefaultSettings().reset_default_settings()

    def song_searched(self, song):
        ListenSongOnline(song).listen_song_online()
