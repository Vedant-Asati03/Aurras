"""
Input Processor for Aurras Music Player.

This module processes user input and routes it to the appropriate handler.
"""

from prompt_toolkit import prompt
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.cursor_shapes import ModalCursorShapeConfig

from aurras.utils.console import console
from aurras.utils.logger import get_logger
from aurras.ui.core.input_lexer import InputLexer
from aurras.utils.exceptions import InvalidInputError
from aurras.ui.completer.history import SongHistoryManager
from aurras.ui.adaptive_completer import AdaptiveCompleter
from aurras.ui.renderers.options_palette import execute_option
from aurras.ui.core.registry import command_registry, shortcut_registry
from aurras.ui.handler import register_all_commands, register_default_shorthands

logger = get_logger("aurras.ui.core.input_processor", log_to_console=False)


class InputProcessor:
    """
    Processes user input and routes it to the appropriate handler.

    This class is responsible for collecting, parsing, and routing user input
    to the appropriate command handlers.
    """

    def __init__(self):
        """Initialize the input processor."""
        register_all_commands()
        register_default_shorthands()

        self.dynamic_search_bar = AdaptiveCompleter()

        self.user_input = None
        self.input_lexer = InputLexer(
            command_registry=command_registry,
            shorthand_registry=shortcut_registry,
        )

    def _set_placeholder_style(self):
        """
        Set placeholder style for the prompt toolkit input based on current theme.

        Returns:
            Style object for prompt_toolkit with theme-consistent colors
        """
        style = HTML(f"<style color='{console.text_muted}'>Search...</style>")

        return style

    def _set_prompt_style(self):
        """
        Set placeholder style for the prompt toolkit input based on current theme.

        Returns:
            Style object for prompt_toolkit with theme-consistent colors
        """
        style = Style.from_dict(
            {
                "prompt": f"bold {console.accent}",
                "command-palette": f"bold {console.accent}",
                "shorthand": f"bold {console.primary}",
                "command": f"bold {console.secondary}",
                "argument": f"{console.text}",
                "text": f"{console.text}",
                "scrollbar.button": f"bg:{console.text}",
                "scrollbar.background": f"bg:{console.background}",
                "completion-menu": f"bg:{console.background} {console.text}",
                "completion-menu.meta.completion": f"bg:{console.background} {console.text_muted}",
            }
        )

        return style

    def get_user_input(self):
        """
        Get user input for song search.

        This method displays the prompt and handles the input collection with
        auto-completion, history suggestions, and theme-consistent styling.

        Raises:
            InvalidInputError: If there's an error processing the user's input
        """
        try:
            self.input_lexer.update_theme_colors()

            self.user_input = (
                prompt(
                    message="󰽸 ",
                    completer=self.dynamic_search_bar,
                    placeholder=self._set_placeholder_style(),
                    style=self._set_prompt_style(),
                    complete_while_typing=True,
                    clipboard=True,
                    mouse_support=True,
                    history=SongHistoryManager(),
                    auto_suggest=AutoSuggestFromHistory(),
                    complete_in_thread=True,
                    vi_mode=True,
                    cursor=ModalCursorShapeConfig(),
                    enable_suspend=True,
                    lexer=self.input_lexer,
                )
                .strip()
                .lower()
            )

            return self.user_input if self.user_input else self.get_user_input()

        except KeyboardInterrupt:
            logger.debug("User interrupted input with Ctrl+C")
            raise

        except Exception as e:
            error_msg = f"Error while getting user input: {str(e)}"
            logger.error(error_msg, exc_info=True)
            console.print_error("An error occurred while processing your input.")

            raise InvalidInputError(error_msg)

    def process_input(self) -> bool:
        """
        Process user input through all available processors.

        Args:
            input_text: User input to process

        Returns:
            True if input was handled, False otherwise
        """
        input_text: str = self.get_user_input()

        if self._process_options_palette(input_text):
            return True

        if self._process_direct_commands(input_text):
            return True

        if self._process_shorthand_commands(input_text):
            return True

        return self._handle_default_input(input_text)

    def _process_direct_commands(self, input_text: str) -> bool:
        """
        Process direct command execution.
        This also includes command palette commands because they are basically direct commands.

        Args:
            input_text: User input text

        Returns:
            True if a command was executed, False otherwise
        """
        command, args = command_registry.parse_command(input_text)

        if command == "cancel":
            return True

        if command and command_registry.execute_command(command, args):
            return True

        return False

    def _process_shorthand_commands(self, input_text: str) -> bool:
        """
        Process shorthand commands.

        Args:
            input_text: User input text

        Returns:
            True if a shorthand was executed, False otherwise
        """
        return shortcut_registry.check_shorthand_commands(input_text)

    def _process_options_palette(self, input_text: str) -> bool:
        """
        Process options palette commands.

        Args:
            input_text: User input text

        Returns:
            True if an option was executed, False otherwise
        """
        return execute_option(input_text)

    def _handle_default_input(self, input_text: str) -> bool:
        """
        Handle input that doesn't match any command patterns.
        Assumes the input is a song search query.

        Args:
            input_text: The input text to process as a song query

        Returns:
            True if input was handled, False otherwise
        """
        if not input_text:
            return False

        try:
            from aurras.utils.command.processors import player_processor

            player_processor.play_song(input_text)
            return True

        except ImportError:
            logger.error("Could not import InputCases", exc_info=True)
            console.print_error("Command handler not available.")
            return False

        except Exception as e:
            logger.error(f"Error handling input: {e}", exc_info=True)
            console.print_error(f"Error handling input: {str(e)}")
            return False
