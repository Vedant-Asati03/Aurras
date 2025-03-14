"""
Command Palette Invoker Module

This module provides a class for invoking the command palette.
"""

from prompt_toolkit.completion import Completer, Completion
from aurras.ui.command_palette import DisplaySettings


class CommandPaletteInvoker(Completer):
    """
    Auto-completion class for the command palette.

    Attributes:
        command_palette_options (list): List of options for the command palette.
    """

    def __init__(self):
        """Initialize the CommandPaletteInvoker class."""
        self.command_palette_options = DisplaySettings().formatted_choices

    def get_completions(self, document, complete_event):
        """
        Get completions for the command palette.

        Parameters:
            document: The document being completed
            complete_event: The completion event

        Returns:
            list: A list of completions
        """
        text_before_cursor = document.text_before_cursor.lstrip()

        # Only provide completions if the input starts with '>'
        if text_before_cursor.startswith(">"):
            completions = [
                Completion(option, start_position=0)
                for option in self.command_palette_options
            ]
            return completions

        return []
