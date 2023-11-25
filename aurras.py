from time import sleep
from sqlitedict import SqliteDict
from prompt_toolkit import prompt
from prompt_toolkit.styles import Style
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import History
import questionary
from rich.text import Text
from rich.console import Console

import config as path
from logger import exception_log
from term_utils import clear_screen
from downloadsong import SongDownloader
from recommendation import SongRecommendations
from playlist import DownloadPlaylist, DeletePlaylist, ImportPlaylist
from playsong import (
    ListenSongOnline,
    ListenSongOffline,
    ListenPlaylistOnline,
    ListenPlaylistOffline,
)


class SongHistory(History):
    """
    History class for handling recent songs in AurrasApp.

    Attributes:
    - database_path (str): Path to the SQLite database file.
    - db_path (str): Database path for storing command history.
    - history_dict (SqliteDict): SqliteDict instance for storing command history.
    """

    def __init__(self):
        """
        Initialize the SqliteHistory class.

        Parameters:
        - database_path (str): Path to the SQLite database file.
        """
        self.history_dict = SqliteDict(path.cache, autocommit=True)
        super().__init__()

    def append_string(self, string):
        """
        Append a string to the command history.

        Parameters:
        - string (str): The string to be appended to the history.
        """
        try:
            index = str(len(self.history_dict))
            self.history_dict[index] = string
        except Exception as e:
            exception_log(f"Error appending string to history: {e}")

    def load_history_strings(self):
        """
        Load history strings from the SQLite database.

        Returns:
        - List[str]: List of history strings.
        """
        try:
            return list(self.history_dict.values())
        except Exception as e:
            exception_log(f"Error loading history strings: {e}")
            return []

    def store_string(self, line):
        """
        Store a string in the command history.

        Parameters:
        - line (str): The string to be stored in the history.
        """
        try:
            index = str(len(self.history_dict))
            self.history_dict[index] = line
        except Exception as e:
            exception_log(f"Error storing string in history: {e}")


class CommandCompleter(Completer):
    """
    Auto-completion class for AurrasApp.

    Attributes:
    - recommendations (list): List of recommendations for auto-completion.
    """

    def __init__(self):
        """
        Initialize the Recommend class.
        """
        self.recommendations = [
            # "Shuffle Play",
            "Play Offline",
            "Download Song",
            "Play Playlist",
            "Delete Playlist",
            "Import Playlist",
            "Download Playlist",
        ]

    def get_completions(self, document, complete_event):
        """
        Get auto-completions.

        Parameters:
        - document: The document being completed.
        - complete_event: The completion event.

        Returns:
        - List[Completion]: List of auto-completions.
        """
        completions = [
            Completion(recommendation, start_position=0)
            for recommendation in self.recommendations
        ]
        return completions


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

    def run(self):
        """Run the AurrasApp"""
        while True:
            self.get_user_input()
            self.handle_user_input(self.song)

    def get_user_input(self):
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
                completer=CommandCompleter(),
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

    def handle_user_input(self, song):
        """
        Handle user input based on the selected song.

        Parameters:
        - song (str): The user-selected song.
        """
        match song:
            case "play offline":
                try:
                    ListenSongOffline().listen_song_offline()
                except Exception as e:
                    exception_log(e)
                    self.console.print("No Downloaded Songs Found!")
                    sleep(1.5)

            case "download song":
                songs_to_download = self.console.input(
                    Text("Enter song name[s]: ", style="#A2DE96")
                )
                list_of_songs_to_download = [
                    song.strip() for song in songs_to_download.split(",")
                ]

                download = SongDownloader(
                    list_of_songs_to_download, path.downloaded_songs
                )
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
                try:
                    DownloadPlaylist().download_playlist()
                except Exception:
                    self.console.print("Playlist Not Found!")
                    sleep(1)

            case _:
                ListenSongOnline(song).listen_song_online()
                self.recommend.recommend_songs()


if __name__ == "__main__":
    aurras_app = AurrasApp()

    try:
        aurras_app.run()

    except KeyboardInterrupt:
        aurras_app.console.print("[bold green]Thanks for using aurras![/]")

    except Exception:
        aurras_app.console.print("[bold red]Oh no! An unknown error occurred.[/]")
        aurras_app.console.print(
            "[bold red]Please report it on https://github.com/Vedant-Asati03/aurras/issues with the following exception traceback:[/]"
        )
        aurras_app.console.print_exception()
