"""
Input Processor for Aurras Music Player.

This module processes user input and routes it to the appropriate handler.
"""

import logging

from prompt_toolkit import prompt
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.cursor_shapes import ModalCursorShapeConfig

from .input_lexer import InputLexer
from .registry import CommandRegistry, ShortcutRegistry
from ..completer.history import SongHistoryManager
from ..adaptive_completer import AdaptiveCompleter
from ..handler import register_all_commands, register_default_shorthands
from ...utils.exceptions import InvalidInputError
from ...themes import get_theme, get_current_theme
from ...utils.theme_helper import ThemeHelper, get_console

logger = logging.getLogger(__name__)
console = get_console()


class InputProcessor:
    """
    Processes user input and routes it to the appropriate handler.

    This class is responsible for collecting, parsing, and routing user input
    to the appropriate command handlers.
    """

    def __init__(self):
        """Initialize the input processor."""
        self.user_input = None
        self.dynamic_search_bar = AdaptiveCompleter()
        self.command_registry = CommandRegistry()
        self.shorthand_registry = ShortcutRegistry(self.command_registry)
        register_all_commands(self.command_registry)
        register_default_shorthands(self.shorthand_registry)

        self.input_lexer = InputLexer(
            command_registry=self.command_registry,
            shorthand_registry=self.shorthand_registry,
        )

    def _set_placeholder_style(self):
        """
        Set placeholder style for the prompt toolkit input based on current theme.

        Returns:
            Style object for prompt_toolkit with theme-consistent colors
        """
        theme_name = get_current_theme()
        theme = get_theme(theme_name)

        style = HTML(f"<style color='{theme.text_muted.hex}'>Search...</style>")

        return style

    def _set_prompt_style(self):
        """
        Set placeholder style for the prompt toolkit input based on current theme.

        Returns:
            Style object for prompt_toolkit with theme-consistent colors
        """
        theme_name = get_current_theme()
        theme = get_theme(theme_name)

        style = Style.from_dict(
            {
                "prompt": f"bold {theme.accent.hex}",
                "command-palette": f"bold {theme.accent.hex}",
                "shorthand": f"bold {theme.primary.hex}",
                "command": f"bold {theme.secondary.hex}",
                "argument": f"{theme.text.hex}",
                "text": f"{theme.text.hex}",
                "scrollbar.button": f"bg:{theme.text.hex}",
                "scrollbar.background": f"bg:{theme.background.hex}",
                "completion-menu": f"bg:{theme.background.hex} {theme.text.hex}",
                "completion-menu.meta.completion": f"bg:{theme.background.hex} {theme.text_muted.hex}",
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
                .strip("?")
                .strip()
                .lower()
            )

            return self.user_input if self.user_input else self.get_user_input()

        except KeyboardInterrupt:
            logger.debug("User interrupted input with Ctrl+C")
            raise

        except Exception as e:
            theme_styles = ThemeHelper.get_theme_colors()
            error_color = theme_styles.get("error", "red")

            error_msg = f"Error while getting user input: {str(e)}"
            logger.error(error_msg, exc_info=True)

            console.print(
                f"[bold {error_color}]An error occurred while processing your input.[/bold {error_color}]"
            )
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

        if self.process_command_palette_input(input_text):
            return True

        if self.process_direct_commands(input_text):
            return True

        if self.process_shorthand_commands(input_text):
            return True

        return self.handle_default_input(input_text)

    def process_command_palette_input(self, input_text: str) -> bool:
        """
        Process input from command palette (commands starting with ">").

        Args:
            input_text: User input text

        Returns:
            True if the input was handled, False otherwise
        """
        if not input_text.startswith(">"):
            return False

        command_action = input_text[1:].strip().lower()

        if command_action == "cancel":
            return True

        # Parse the command palette selection
        if ":" in command_action:
            try:
                # Use the correct import path to the command palette
                from ..command_palette import CommandPalette

                # Get the command name from the input
                command_name = command_action.split(":", 1)[0].strip()

                # Execute the command using the CommandPalette class
                cmd_palette = CommandPalette()
                return cmd_palette.execute_command(command_name)
            except ImportError:
                logger.error("Command palette module not found", exc_info=True)
                theme_styles = ThemeHelper.get_theme_colors()
                error_color = theme_styles.get("error", "red")
                console.print(
                    f"[bold {error_color}]Command palette not available.[/bold {error_color}]"
                )
            except Exception as e:
                logger.error(
                    f"Error executing command palette action: {e}", exc_info=True
                )
                theme_styles = ThemeHelper.get_theme_colors()
                error_color = theme_styles.get("error", "red")
                console.print(
                    f"[bold {error_color}]Error executing command: {str(e)}[/bold {error_color}]"
                )

        return False

    def process_direct_commands(self, input_text: str) -> bool:
        """
        Process direct command execution.

        Args:
            input_text: User input text

        Returns:
            True if a command was executed, False otherwise
        """
        command, args = self.command_registry.parse_command(input_text)

        if command and self.command_registry.execute_command(command, args):
            return True

        return False

    def process_shorthand_commands(self, input_text: str) -> bool:
        """
        Process shorthand commands.

        Args:
            input_text: User input text

        Returns:
            True if a shorthand was executed, False otherwise
        """
        return self.shorthand_registry.check_shorthand_commands(input_text)

    def handle_default_input(self, input_text: str) -> bool:
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
            from ...utils.command.processors.player import processor

            processor.play_song(input_text)

            return True
        except ImportError:
            logger.error("Could not import InputCases", exc_info=True)
            theme_styles = ThemeHelper.get_theme_colors()
            error_color = theme_styles.get("error", "red")
            console.print(
                f"[bold {error_color}]Error: Command handler not available[/bold {error_color}]"
            )
            return False
        except Exception as e:
            logger.error(f"Error handling input: {e}", exc_info=True)
            theme_styles = ThemeHelper.get_theme_colors()
            error_color = theme_styles.get("error", "red")
            console.print(
                f"[bold {error_color}]Error handling input: {str(e)}[/bold {error_color}]"
            )
            return False


input_processor = InputProcessor()
