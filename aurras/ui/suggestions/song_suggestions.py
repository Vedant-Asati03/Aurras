from prompt_toolkit.completion import Completer, Completion
from ...services.youtube.search import (
    SearchFromYoutube,
)


class SongCompleter(Completer):
    """
    Auto-completion class for AurrasApp commands.

    Attributes:
    - command_recommendations (list): List of recommended commands for auto-completion.
    """

    def __init__(self):
        """
        Initializes the CommandCompleter class.
        """
        self.song_recommendation = None
        self.selected_song_url = None

    def get_completions(self, document, complete_event):
        """
        Gets auto-completions for AurrasApp commands.

        Parameters:
        - document: The document being completed.
        - complete_event: The completion event.

        Returns:
        - List[Completion]: A list of auto-completions.
        """
        song_name_typing = document.text_before_cursor.lstrip()

        if song_name_typing == "":
            return []

        search_song = SearchFromYoutube(song_name_typing)
        try:
            search_song.search_from_youtube()
        except Exception:
            return []

        self.song_recommendation = search_song.song_name_searched

        completions = [
            Completion(self.song_recommendation, start_position=0)
            # for command in self.song_recommendations
        ]
        return completions
