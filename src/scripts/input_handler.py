from rich.text import Text
from rich.console import Console
from prompt_toolkit import prompt
from prompt_toolkit.styles import Style
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
import questionary

from lib.term_utils import clear_screen
import config.config as path
from config.default_settings import CreateDefaultSettings
from src.command_palette.command_palette_config import DisplaySettings
from src.search_utilities.search_utils import SongHistory, DynamicCompleter
from src.scripts.downloadsong import SongDownloader
from src.scripts.playlist.download_playlist import DownloadPlaylist
from src.scripts.playlist.delete_playlist import DeletePlaylist
from src.scripts.playlist.import_playlist.import_from_spotify import (
    ImportSpotifyPlaylist,
)
from src.scripts.playsong.listen_online import ListenSongOnline, ListenPlaylistOnline
from src.scripts.playsong.listen_offline import ListenSongOffline, ListenPlaylistOffline


class HandleUserInput:
    def __init__(self):
        """
        Initialize the AurrasApp class.
        """
        self.song = None
        self.console = Console()
        self.dynamic_completer = DynamicCompleter()

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
                completer=self.dynamic_completer,
                placeholder="Search Song",
                style=style,
                complete_while_typing=True,
                clipboard=True,
                mouse_support=True,
                history=SongHistory(),
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

        match self.song:
            case None | "":
                self._get_user_input()

            case "play offline":
                ListenSongOffline().listen_song_offline()

            case "download song":
                songs_to_download = self.console.input(
                    Text("Enter song name[s]: ", style="#A2DE96")
                ).split(",")

                download = SongDownloader(songs_to_download, path.downloaded_songs)
                download.download_song()

            case "play playlist":
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

            case "delete playlist":
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

            case "import playlist":
                ImportSpotifyPlaylist().import_spotify_playlist()

            case "download playlist":
                DownloadPlaylist().download_playlist()

            case "settings":
                DisplaySettings().display_settings()

            case ">reset":
                CreateDefaultSettings().reset_default_settings()

            case _:
                ListenSongOnline(self.song).listen_song_online()


class HandleInputCases:
    def __init__(self) -> None:
        pass


def case_play_offline(self):
    ...
