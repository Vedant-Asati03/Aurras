from prompt_toolkit.completion import Completer, Completion

from config import path
from config.config import Config
from src.scripts.playlist.select_playlist_from_db import Select


class SuggestPlaylists(Completer):
    """
    Auto-completion class for AurrasApp commands.

    Attributes:
    - command_recommendations (list): List of recommended commands for auto-completion.
    """

    def __init__(self):
        """
        Initializes the CommandCompleter class.
        """
        self.config = Config()
        self.select = Select()

    def get_completions(self, document, complete_event):
        """
        Gets auto-completions for AurrasApp commands.

        Parameters:
        - document: The document being completed.
        - complete_event: The completion event.

        Returns:
        - List[Completion]: A list of auto-completions.
        """
        saved_playlists_to_suggest = self.select.load_playlist_from_db()
        downloaded_playlists_to_recommend = self.config.list_directory(
            path.downloaded_playlists
        )
        text_before_cursor = document.text_before_cursor.lower()

        if (
            text_before_cursor.startswith("pn,")
            | text_before_cursor.startswith("dp,")
            | text_before_cursor.startswith("rs,")
        ):
            completions = [
                Completion(command, start_position=0)
                for command in saved_playlists_to_suggest
            ]
            return completions

        if text_before_cursor.startswith("pf,") | text_before_cursor.startswith("rd,"):
            completions = [
                Completion(command, start_position=0)
                for command in downloaded_playlists_to_recommend
            ]
            return completions

        return []
