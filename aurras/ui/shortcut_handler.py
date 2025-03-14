from ..ui.command_handler import InputCases


class HandleShortcutInputs:
    def __init__(self, user_input: str) -> None:
        self.case = InputCases()
        # Only split if the first part looks like a shortcut command
        if "," in user_input and user_input.split(",")[0].strip() in [
            "d",
            "dp",
            "pn",
            "pf",
            "rs",
            "rd",
        ]:
            self.user_input_as_list = user_input.split(",")
        else:
            self.user_input_as_list = [user_input]

    def handle_shortcut_input(self):
        # Debug print to see what's being processed
        print(f"> Shortcut check: {self.user_input_as_list}")

        # Only treat as shortcut if it starts with a known shortcut command
        first_part = self.user_input_as_list[0].strip()

        if first_part == "d" and len(self.user_input_as_list) > 1:
            self.case.download_song(self.user_input_as_list[1:])
            return "shortcut_used"

        elif first_part == "dp" and len(self.user_input_as_list) > 1:
            self.case.download_playlist(self.user_input_as_list[1].strip())
            return "shortcut_used"

        elif first_part in ["pn", "pf"] and len(self.user_input_as_list) > 1:
            self.case.play_playlist(first_part[1], self.user_input_as_list[1].strip())
            return "shortcut_used"

        elif first_part in ["rs", "rd"] and len(self.user_input_as_list) > 1:
            self.case.delete_playlist(first_part[1], self.user_input_as_list[1].strip())
            return "shortcut_used"

        return "shortcut_not_used"

    def _contains_input(self, *options):
        if len(self.user_input_as_list) == 0:
            return False
        return self.user_input_as_list[0].strip() in options
