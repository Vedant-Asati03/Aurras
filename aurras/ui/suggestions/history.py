from sqlitedict import SqliteDict
from prompt_toolkit.history import History

# Replace absolute import with relative import
from ...utils.path_manager import PathManager

_path_manager = PathManager()

from ...utils.logger import exception_log


class SuggestSongsFromHistory(History):
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
        self.history_dict = SqliteDict(_path_manager.cache_db, autocommit=True)
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
