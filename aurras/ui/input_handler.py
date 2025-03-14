from prompt_toolkit import prompt
from prompt_toolkit.styles import Style
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
import time

from ..utils.terminal import clear_screen
from ..ui.command_handler import InputCases
from ..ui.search_bar import DynamicSearchBar
from ..ui.suggestions.history import SuggestSongsFromHistory
from ..ui.command_palette import DisplaySettings
from ..ui.shortcut_handler import HandleShortcutInputs
from ..player.online import ListenSongOnline
from ..player.queue import QueueManager


class HandleUserInput:
    def __init__(self):
        """
        Initialize the AurrasApp class.
        """
        self.user_input = None
        self.case = InputCases()
        self.dynamic_search_bar = DynamicSearchBar()
        self.queue_manager = QueueManager()

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
        self.user_input = (
            prompt(
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
        print(f"\n> Processing input: '{self.user_input}'")

    def handle_user_input(self):
        """
        Handle user input based on the selected song.
        """
        self._get_user_input()

        # If input is empty, get new input
        if not self.user_input:
            return

        # First check for comma-separated songs - this should take highest priority
        if "," in self.user_input:
            print(f"> Detected comma-separated input: '{self.user_input}'")
            songs = [s.strip() for s in self.user_input.split(",") if s.strip()]
            if songs:
                print(f"> Playing sequence of {len(songs)} songs:")
                for i, song in enumerate(songs):
                    print(f"  {i + 1}. {song}")

                try:
                    # Play each song directly in sequence
                    for i, song in enumerate(songs):
                        print(f"\n> Now playing: {song} [{i + 1}/{len(songs)}]")
                        player = ListenSongOnline(song)
                        player.listen_song_online()
                except KeyboardInterrupt:
                    print("\n> Playback interrupted by user")
                except Exception as e:
                    print(f"\n> Error during playback: {e}")

                return

        # Only check shortcuts if not comma-separated
        check_if_shortcut_used = HandleShortcutInputs(
            self.user_input
        ).handle_shortcut_input()

        if check_if_shortcut_used == "shortcut_not_used":
            actions = {
                "help": self.case.display_help,
                "play_offline": self.case.play_offline,
                "download_song": self.case.download_song,
                "play_playlist": self.case.play_playlist,
                "delete_playlist": self.case.delete_playlist,
                "import_playlist": self.case.import_playlist,
                "download_playlist": self.case.download_playlist,
                "queue": self.case.show_queue,
                "clear_queue": self.case.clear_queue,
            }

            # Check for commands
            if self.user_input in actions:
                print(f"> Executing command: {self.user_input}")
                actions[self.user_input]()
                return

            # Default to single song
            else:
                print(f"> Playing single song: {self.user_input}")
                self.case.song_searched(self.user_input)
                return
