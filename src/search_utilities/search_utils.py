from sqlitedict import SqliteDict
from prompt_toolkit.history import History
from prompt_toolkit.completion import Completer, Completion

import config.config as path
from lib.logger import exception_log
from src.command_palette.command_palette_config import DisplaySettings


class SongHistory(History):
    """
    A class to manage the command history of recent songs in AurrasApp.

    Attributes:
    - database_path (str): The path to the SQLite database file.
    - db_path (str): The database path for storing command history.
    - history_dict (SqliteDict): An instance of SqliteDict for storing command history.
    """

    def __init__(self):
        """
        Initializes the SongHistory class.

        Parameters:
        - database_path (str): The path to the SQLite database file.
        """
        self.history_dict = SqliteDict(path.cache, autocommit=True)
        super().__init__()

    def append_string(self, command):
        """
        Appends a string to the command history.

        Parameters:
        - command (str): The string to be appended to the history.
        """
        try:
            index = str(len(self.history_dict))
            self.history_dict[index] = command
        except Exception as e:
            exception_log(f"Error appending string to history: {e}")

    def load_history_strings(self):
        """
        Loads history strings from the SQLite database.

        Returns:
        - List[str]: A list of history strings.
        """
        try:
            return list(self.history_dict.values())
        except Exception as e:
            exception_log(f"Error loading history strings: {e}")
            return []

    def store_string(self, command):
        """
        Stores a string in the command history.

        Parameters:
        - command (str): The string to be stored in the history.
        """
        try:
            index = str(len(self.history_dict))
            self.history_dict[index] = command
        except Exception as e:
            exception_log(f"Error storing string in history: {e}")


class CommandCompleter(Completer):
    """
    Auto-completion class for AurrasApp commands.

    Attributes:
    - command_recommendations (list): List of recommended commands for auto-completion.
    """

    def __init__(self):
        """
        Initializes the CommandCompleter class.
        """
        self.command_recommendations = [
            # "Shuffle Play",
            "Play Offline",
            "Download Song",
            "Play Playlist",
            "Delete Playlist",
            "Import Playlist",
            "Download Playlist",
            "Settings",
        ]

    def get_completions(self, document, complete_event):
        """
        Gets auto-completions for AurrasApp commands.

        Parameters:
        - document: The document being completed.
        - complete_event: The completion event.

        Returns:
        - List[Completion]: A list of auto-completions.
        """
        completions = [
            Completion(command, start_position=0)
            for command in self.command_recommendations
        ]
        return completions


class CustomCompleter(Completer):
    """
    Auto-completion class for a custom scenario.

    Attributes:
    - custom_options (list): List of custom options for auto-completion.
    """

    def __init__(self):
        """
        Initializes the CustomCompleter class.
        """
        self.custom_options = None

    def get_completions(self, document, complete_event):
        """
        Gets auto-completions for a custom scenario.

        Parameters:
        - document: The document being completed.
        - complete_event: The completion event.

        Returns:
        - List[Completion]: A list of auto-completions.
        """
        self.custom_options = DisplaySettings().formatted_choices
        text_before_cursor = document.text_before_cursor.lstrip()

        # Only provide completions if the input starts with '>'
        if text_before_cursor.startswith(">"):
            completions = [
                Completion(option, start_position=0) for option in self.custom_options
            ]
            return completions

        return []


class DynamicCompleter(Completer):
    def __init__(self):
        # self.completers = completers
        self.command_completer = CommandCompleter()
        self.custom_completer = CustomCompleter()

    def get_completions(self, document, complete_event):
        current_completer = self.command_completer  # Default to the first completer

        if document.text.startswith(">"):
            current_completer = (
                self.custom_completer
            )  # Switch to the second completer when input starts with '>'

        return current_completer.get_completions(document, complete_event)
