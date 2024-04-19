from prompt_toolkit.completion import Completer, Completion


class SuggestAppFeatures(Completer):
    """
    Auto-completion class for AurrasApp commands.

    Attributes:
    - command_recommendations (list): List of recommended commands for auto-completion.
    """

    def __init__(self):
        """
        Initializes the CommandCompleter class.
        """
        self.app_features = [
            "Play_Offline",
            "Download_Song",
            "Play_Playlist",
            "Delete_Playlist",
            "Import_Playlist",
            "Download_Playlist",
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
        text_before_cursor = document.text_before_cursor

        # Only provide completions if the input starts with ' '
        if text_before_cursor.startswith("?"):
            completions = [
                Completion(command, start_position=0)
                for command in self.app_features
            ]
            return completions
        return []
