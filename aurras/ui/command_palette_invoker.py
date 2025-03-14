"""
Command Palette Invoker Module

This module provides a class for invoking the command palette via completion.
"""

from prompt_toolkit.completion import Completer, Completion
from .command_palette import CommandPalette


class CommandPaletteInvoker(Completer):
    """
    Auto-completion class for the command palette.

    This class shows command palette options when '>' is typed.
    """

    def __init__(self):
        """Initialize the CommandPaletteInvoker class."""
        self.command_palette = CommandPalette()
        self.commands = self.command_palette.commands

    def get_completions(self, document, complete_event):
        """
        Get completions for the command palette.

        Parameters:
            document: The document being completed
            complete_event: The completion event

        Returns:
            list: A list of completions
        """
        text_before_cursor = document.text_before_cursor.lower()

        # Only provide completions if the input starts with '>'
        if text_before_cursor.startswith(">"):
            # Get the text after > to allow filtering
            search_text = text_before_cursor[1:].strip().lower()

            for cmd_id, cmd in self.commands.items():
                name = cmd["name"]
                desc = cmd["description"]
                display = f"{name}: {desc}"

                # Filter commands based on search text if any
                if (
                    not search_text
                    or search_text in name.lower()
                    or search_text in desc.lower()
                ):
                    # Ensure completion replaces the entire input
                    yield Completion(
                        display,
                        start_position=-len(text_before_cursor),
                        display=display,
                        display_meta="Command",
                    )

            # Always add a cancel option
            yield Completion(
                "Cancel",
                start_position=-len(text_before_cursor),
                display="Cancel: Return to main interface",
                display_meta="Command",
            )
