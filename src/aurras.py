"""
...
"""

import sys
from pathlib import Path
from rich.text import Text
from rich.console import Console
from prompt_toolkit import prompt
from prompt_toolkit.styles import Style
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
import questionary

# Add the project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import config.config as path
from config.default_settings import CreateDefaultSettings
from utils.decorators import handle_exceptions
from lib.logger import exception_log
from lib.term_utils import clear_screen
from lib.recommendation import SongRecommendations
from src.command_palette.command_palette_config import DisplaySettings
from src.search_utilities.search_utils import SongHistory, DynamicCompleter
from src.scripts.downloadsong import SongDownloader
from src.scripts.playlist import DownloadPlaylist, DeletePlaylist, ImportPlaylist
from src.scripts.playsong import (
    ListenSongOnline,
    ListenSongOffline,
    ListenPlaylistOnline,
    ListenPlaylistOffline,
)
from exceptions.exceptions import (
    PlaylistNotFoundError,
    SongsNotFoundError,
    NotAuthenticatedError,
)


class AurrasApp:
    """
    AurrasApp class for handling the Aurras music player application.

    Attributes:
    - console (Console): Rich Console for printing messages.
    - recent_songs (RecentSongs): Instance of the RecentSongs class for handling command history.
    """

    def __init__(self):
        """
        Initialize the AurrasApp class.

        Parameters:
        - recent_songs (RecentSongs): Instance of the RecentSongs
        class for handling command history.
        """
        self.song = None
        self.console = Console()
        self.recommend = SongRecommendations()
        self.dynamic_completer = DynamicCompleter()

    @handle_exceptions
    def run(self):
        """Run the AurrasApp"""
        while True:
            self._get_user_input()
            self._handle_user_input(self.song)

    def _get_user_input(self):
        """
        Get user input for song search.

        Returns:
        - str: The user-inputted song.
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

    def _handle_user_input(self, song):
        """
        Handle user input based on the selected song.

        Parameters:
        - song (str): The user-selected song.
        """
        match song:
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

                match online_offline:
                    case "Play Online":
                        ListenPlaylistOnline().listen_playlist_online()
                    case "Play Offline":
                        ListenPlaylistOffline().listen_playlist_offline()

            case "delete playlist":
                online_offline = questionary.select(
                    "Select Playlist to Delete",
                    choices=["Saved Playlists", "Downloaded Playlists"],
                ).ask()

                match online_offline:
                    case "Saved Playlists":
                        DeletePlaylist().delete_saved_playlist()
                    case "Downloaded Playlists":
                        DeletePlaylist().delete_downloaded_playlist()

            case "import playlist":
                ImportPlaylist().import_playlist()

            case "download playlist":
                DownloadPlaylist().download_playlist()

            case "settings":
                DisplaySettings().display_settings()

            case ">reset":
                CreateDefaultSettings().reset_default_settings()

            case _:
                ListenSongOnline(song).listen_song_online()
                self.recommend.recommend_songs()


if __name__ == "__main__":
    aurras_app = AurrasApp()

    # Apply the handle_exceptions decorator to the run method
    run_with_exceptions = handle_exceptions(aurras_app.run)

    try:
        run_with_exceptions()

    except KeyboardInterrupt:
        aurras_app.console.print("[bold green]Thanks for using aurras![/]")

    except TimeoutError:
        aurras_app.console.print(
            "[bold red]Please connect to stable internet connection![/]"
        )

    # except Exception:
    #     aurras_app.console.print("[bold red]Oh no! An unknown error occurred.[/]")
    #     aurras_app.console.print(
    #         "[bold red]Please report it on https://github.com/Vedant-Asati03/aurras/issues with the following exception traceback:[/]"
    #     )
    #     aurras_app.console.print_exception()

    except Exception as e:
        # Catch the specific exception raised by the handle_exceptions decorator
        if isinstance(
            e, (PlaylistNotFoundError, SongsNotFoundError, NotAuthenticatedError)
        ):
            aurras_app.console.print(f"[bold red]Error: {e}[/]")
            # Handle specific exceptions here
        else:
            # Handle other unexpected exceptions
            aurras_app.console.print("[bold red]Oh no! An unknown error occurred.[/]")
            aurras_app.console.print(
                "[bold red]Please report it on https://github.com/Vedant-Asati03/aurras/issues with the following exception traceback:[/]"
            )
            aurras_app.console.print_exception()
