from typing import List, Tuple

from aurras.ui.completer.base import BaseCompleter
from aurras.ui.renderers.command_palette import CommandPalette


class CommandCompleter(BaseCompleter):
    """
    Auto-completion class for the command palette.

    This class shows command palette options when '>' is typed.
    """

    def __init__(self):
        """Initialize the CommandCompleter class."""
        self.command_palette = CommandPalette()
        self.commands = self.command_palette.commands

    def get_suggestions(self, text: str) -> List[Tuple[str, str]]:
        """
        Get command palette suggestions.

        Args:
            text: The input text with prefix

        Returns:
            List of tuples (command_display, "Command")
        """
        if text.startswith(">"):
            search_text = text[1:].strip().lower()
            result = []

            for cmd_id, cmd in self.commands.items():
                name = cmd["name"]
                desc = cmd["description"]
                display = f"{name}: {desc}"

                if (
                    not search_text
                    or search_text in name.lower()
                    or search_text in desc.lower()
                ):
                    result.append((display, "Command"))

            # Always add a cancel option
            result.append(("Cancel", "Command"))

            return result

        return []
