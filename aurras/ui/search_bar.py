from prompt_toolkit.completion import Completer, WordCompleter

from .suggestions.feature_suggestions import SuggestAppFeatures
# from .invoke_command_palette import CommandPaletteInvoker
from .suggestions.song_suggestions import SongCompleter
from .suggestions.playlist_suggestions import SuggestPlaylists


class DynamicSearchBar(Completer):
    def __init__(self):
        self.suggest_app_features = SuggestAppFeatures()
        # self.command_palette_invoker = CommandPaletteInvoker()
        self.song_completer = SongCompleter()
        self.suggest_playlists = SuggestPlaylists()

    #     self.custom_message = ""

    # def _show_message_command_palette(self):
    #     self.custom_message = "Command Palette| "

    # def _show_message_search_app_features(self):
    #     self.custom_message = "Search app features| "

    def get_completions(self, document, complete_event):
        current_completer = self.song_completer  # Default to the first completer

        text_before_cursor = document.text_before_cursor.lower()

        if (
            text_before_cursor.startswith("pn,")
            | text_before_cursor.startswith("pf,")
            | text_before_cursor.startswith("dp,")
            | text_before_cursor.startswith("rs,")
            | text_before_cursor.startswith("rd,")
        ):
            current_completer = (
                self.suggest_playlists
            )  # Suggest app features when input starts with 'pn,' or 'pf,'
        # elif text_before_cursor.startswith(">"):
        #     current_completer = (
        #         self.command_palette_invoker
        #     )  # Switch to command palette when input starts with '>'
            # self._show_message_command_palette()
        elif text_before_cursor.startswith("?"):
            current_completer = (
                self.suggest_app_features
            )  # Suggest app features when input starts with '?'
            # self._show_message_search_app_features()

        completions = current_completer.get_completions(document, complete_event)

        completion_texts = [completion.text for completion in completions]

        return WordCompleter(
            completion_texts, ignore_case=True, match_middle=True
        ).get_completions(document, complete_event)
