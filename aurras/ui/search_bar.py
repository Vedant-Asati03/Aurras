from prompt_toolkit.completion import Completer, WordCompleter

from .suggestions.feature_suggestions import SuggestAppFeatures
from .command_palette_invoker import CommandPaletteInvoker
from .suggestions.song_suggestions import SongCompleter
from .suggestions.playlist_suggestions import SuggestPlaylists


class DynamicSearchBar(Completer):
    def __init__(self):
        self.suggest_app_features = SuggestAppFeatures()
        self.command_palette_invoker = CommandPaletteInvoker()
        self.song_completer = SongCompleter()
        self.suggest_playlists = SuggestPlaylists()

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
            current_completer = self.suggest_playlists
        elif text_before_cursor.startswith(">"):
            current_completer = self.command_palette_invoker
        elif text_before_cursor.startswith("?"):
            current_completer = self.suggest_app_features

        return current_completer.get_completions(document, complete_event)
