from rich.text import Text
from rich.console import Console
from prompt_toolkit import prompt
from prompt_toolkit.styles import Style
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
import questionary

from lib.term_utils import clear_screen
from config import path
from config.settings.create_default_settings import CreateDefaultSettings
from src.command_palette.command_palette_config import DisplaySettings
from src.search_utilities.dynamic_search_bar import DynamicSearchBar
from src.search_utilities.suggest_songs_from_history import SuggestSongsFromHistory
from src.scripts.downloadsong import SongDownloader
from .playlist.download_playlist import DownloadPlaylist
from .playlist.delete_playlist import DeletePlaylist
from .playlist.import_playlist.import_from_spotify import (
    ImportSpotifyPlaylist,
)
from .playsong.listen_online import ListenSongOnline, ListenPlaylistOnline
from .playsong.listen_offline import ListenSongOffline, ListenPlaylistOffline


class HandleUserInput:
    def __init__(self):
        """
        Initialize the AurrasApp class.
        """
        self.song = None
        self.case = HandleInputCases()
        self.dynamic_search_bar = DynamicSearchBar()

    def _get_user_input(self):
        """
        Get user input for song search.
        """
        clear_screen()
        style = Style.from_dict(
            {
                "placeholder": "ansilightgray",
            }
        )

        self.song = (
            prompt(
                # self.dynamic_search_bar.custom_message,
                completer=self.dynamic_search_bar,
                placeholder="Search Song",
                style=style,
                complete_while_typing=True,
                clipboard=True,
                mouse_support=True,
                history=SuggestSongsFromHistory(),
                auto_suggest=AutoSuggestFromHistory(),
            )
            .strip()
            .lower()
        )
        clear_screen()

    def handle_user_input(self):
        """
        Handle user input based on the selected song.
        """
        self._get_user_input()

        actions = {
            "": self._get_user_input,
            "play offline": self.case.play_offline,
            "download song": self.case.download_song,
            "play playlist": self.case.play_playlist,
            "delete playlist": self.case.delete_playlist,
            "import playlist": self.case.import_playlist,
            "download playlist": self.case.download_playlist,
            "settings": self.case.settings,
            ">reset": self.case.reset_setting,
        }

        actions.get(self.song, lambda: self.case.song_searched(self.song))()


class HandleInputCases:
    def __init__(self) -> None:
        self.console = Console()

    def play_offline(self):
        ListenSongOffline().listen_song_offline()

    def download_song(self):
        songs_to_download = self.console.input(
            Text("Enter song name[s]: ", style="#A2DE96")
        ).split(",")

        download = SongDownloader(songs_to_download, path.downloaded_songs)
        download.download_song()

    def play_playlist(self):
        online_offline = questionary.select(
            "", choices=["Play Online", "Play Offline"]
        ).ask()
        listen_playlist_online = ListenPlaylistOnline()
        listen_playlist_offline = ListenPlaylistOffline()

        match online_offline:
            case "Play Online":
                listen_playlist_online.listen_playlist_online()
            case "Play Offline":
                listen_playlist_offline.listen_playlist_offline()

    def delete_playlist(self):
        online_offline = questionary.select(
            "Select Playlist to Delete",
            choices=["Saved Playlists", "Downloaded Playlists"],
        ).ask()
        delete_playlist = DeletePlaylist()

        match online_offline:
            case "Saved Playlists":
                delete_playlist.delete_saved_playlist()
            case "Downloaded Playlists":
                delete_playlist.delete_downloaded_playlist()

    def import_playlist(self):
        ImportSpotifyPlaylist().import_spotify_playlist()

    def download_playlist(self):
        DownloadPlaylist().download_playlist()

    def settings(self):
        DisplaySettings().display_settings()

    def reset_setting(self):
        CreateDefaultSettings().reset_default_settings()

    def song_searched(self, song):
        ListenSongOnline(song).listen_song_online()
