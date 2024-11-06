from prompt_toolkit import prompt
from prompt_toolkit.styles import Style
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

from lib.term_utils import clear_screen
from src.scripts.inputs.input_cases import InputCases
from src.search_utilities.dynamic_search_bar import DynamicSearchBar
from src.search_utilities.suggest_songs_from_history import SuggestSongsFromHistory
from src.command_palette.command_palette_config import DisplaySettings
from src.scripts.inputs.shortcut_input_handler import HandleShortcutInputs


class HandleUserInput:
    def __init__(self):
        """
        Initialize the AurrasApp class.
        """
        self.user_input = None
        self.case = InputCases()
        self.dynamic_search_bar = DynamicSearchBar()
        # self.command_palette_options = DisplaySettings().formatted_choices

    def _set_placeholder_style(self):
        style = Style.from_dict(
            {
                "placeholder": "ansilightgray",
            }
        )

        return style

    def _get_user_input(self):
        """
        Get user input for song search.
        """
        clear_screen()

        self.user_input = (
            prompt(
                # message=self.dynamic_search_bar.custom_message,
                completer=self.dynamic_search_bar,
                placeholder="Search Song",
                style=self._set_placeholder_style(),
                complete_while_typing=True,
                clipboard=True,
                mouse_support=True,
                history=SuggestSongsFromHistory(),
                auto_suggest=AutoSuggestFromHistory(),
                complete_in_thread=True,
            )
            .strip("?")
            .strip(">")
            .strip()
            .lower()
        )
        clear_screen()

    def _is_empty_input(self):
        self._get_user_input()

    def handle_user_input(self):
        """
        Handle user input based on the selected song.
        """
        self._get_user_input()
        check_if_shortcut_used = HandleShortcutInputs(
            self.user_input
        ).handle_shortcut_input()

        if check_if_shortcut_used == "shortcut_not_used":
            actions = {
                "": self._get_user_input,
                "play_offline": self.case.play_offline,
                "download_song": self.case.download_song,
                "play_playlist": self.case.play_playlist,
                "delete_playlist": self.case.delete_playlist,
                "import_playlist": self.case.import_playlist,
                "download_playlist": self.case.download_playlist,
                # "settings": self.case.settings,
                # "reset": self.case.reset_setting,
            }

            actions.get(
                self.user_input, lambda: self.case.song_searched(self.user_input)
            )()
