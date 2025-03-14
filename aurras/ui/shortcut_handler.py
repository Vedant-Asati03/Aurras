from ..ui.command_handler import InputCases


class HandleShortcutInputs:
    def __init__(self, user_input: str) -> None:
        self.case = InputCases()
        self.user_input_as_list = user_input.split(",")

    def handle_shortcut_input(self):
        match self.user_input_as_list:
            case ["d", *songs]:
                self.case.download_song(songs)

            case ["dp", playlist_name]:
                self.case.download_playlist(playlist_name.strip())

            case [shortcut_key, playlist_name]:
                if self._contains_input("pn", "pf"):
                    self.case.play_playlist(
                        shortcut_key[1].strip(), playlist_name.strip()
                    )
                elif self._contains_input("rs", "rd"):
                    self.case.delete_playlist(
                        shortcut_key[1].strip(), playlist_name.strip()
                    )

            case _:
                return "shortcut_not_used"

        return "shortcut_used"

    def _contains_input(self, *options):
        return any(option in self.user_input_as_list for option in options)
