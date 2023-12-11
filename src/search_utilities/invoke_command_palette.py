from prompt_toolkit.completion import Completer, Completion
from src.command_palette.command_palette_config import DisplaySettings


class CommandPaletteInvoker(Completer):
    """
    Auto-completion class for a custom scenario.

    Attributes:
    - custom_options (list): List of custom options for auto-completion.
    """

    def __init__(self):
        """
        Initializes the CustomCompleter class.
        """
        self.custom_options = None

    def get_completions(self, document, complete_event) -> list:
        """
        Gets auto-completions for a custom scenario.

        Parameters:
        - document: The document being completed.
        - complete_event: The completion event.

        Returns:
        - List[Completion]: A list of auto-completions.
        """
        self.custom_options = DisplaySettings().formatted_choices
        text_before_cursor = document.text_before_cursor.lstrip()

        # Only provide completions if the input starts with '>'
        if text_before_cursor.startswith(">"):
            completions = [
                Completion(option, start_position=0) for option in self.custom_options
            ]
            return completions

        return []
