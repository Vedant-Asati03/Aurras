from typing import List, Tuple

from aurras.core.settings import SETTINGS
from aurras.ui.renderers import command_palette
from aurras.ui.completer.base import BaseCompleter


class CommandCompleter(BaseCompleter):
    """
    Auto-completion class for the command palette.

    This class shows command palette options when '>' is typed.
    """

    def __init__(self):
        """Initialize the CommandCompleter class."""
        self.commands = command_palette.create_commands_mapping()

    def get_suggestions(self, text: str) -> List[Tuple[str, str]]:
        """
        Get command palette suggestions.

        Args:
            text: The input text with prefix

        Returns:
            List of tuples (command_display, "Command")
        """
        if text.startswith(SETTINGS.command_palette_key):
            search_text = text[1:].strip().lower()
            result = []

            for name, desc in self.commands.items():
                if (
                    not search_text
                    or search_text in name.lower()
                    or search_text in desc.lower()
                ):
                    result.append((name, desc))

            # Always add a cancel option
            result.append(("cancel", "close palette"))

            return result

        return []
