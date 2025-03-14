from prompt_toolkit import prompt
from prompt_toolkit.styles import Style
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

from ..utils.terminal import clear_screen
from ..ui.command_handler import InputCases
from ..ui.search_bar import DynamicSearchBar
from ..ui.suggestions.history import SuggestSongsFromHistory
from ..ui.command_palette import DisplaySettings
from ..ui.shortcut_handler import HandleShortcutInputs


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
                "help": self.case.display_help,
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
