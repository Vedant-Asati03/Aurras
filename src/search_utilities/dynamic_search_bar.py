from prompt_toolkit.completion import Completer, WordCompleter

from .feature_suggestions import SuggestAppFeatures
from .invoke_command_palette import CommandPaletteInvoker
from .insearch_song_suggestions import SongCompleter


class DynamicSearchBar(Completer):
    def __init__(self):
        self.command_completer = SuggestAppFeatures()
        self.custom_completer = CommandPaletteInvoker()
        self.song_completer = SongCompleter()
        self.custom_message = ""

    def get_completions(self, document, complete_event):
        current_completer = self.song_completer  # Default to the first completer

        if document.text.startswith(">"):
            current_completer = (
                self.custom_completer
            )  # Switch to command palette when input starts with '>'
            self.custom_message = "Command Palette"
        elif document.text.startswith("?"):
            current_completer = (
                self.command_completer
            )  # Suggest app features when input starts with '?'
            self.custom_message = "Search app features"

        completions = current_completer.get_completions(document, complete_event)

        completion_texts = [completion.text for completion in completions]

        return WordCompleter(
            completion_texts,
            ignore_case=True,
            match_middle=True
        ).get_completions(document, complete_event)
