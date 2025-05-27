"""
Console manager for terminal UI rendering.

This module provides utilities for working with the terminal console
and accessing theme information for rendering.
"""

from typing import Optional, Any

from rich.panel import Panel
from rich.table import Table
from rich.console import Console

from aurras.utils.logger import get_logger
from aurras.themes.adapters import theme_to_rich_theme
from aurras.themes.manager import get_theme, get_current_theme, set_current_theme

logger = get_logger("aurras.utils.console.manager", log_to_console=False)

# Global console instance for consistent styling
_console: Optional["ThemedConsole"] = None


class ThemedConsole(Console):
    """
    Enhanced console with theme integration.

    This class extends Rich's Console with theme-aware methods to reduce
    boilerplate code across the application and provides factory methods
    for common Rich components with theme integration.
    """

    def __init__(self, *args, **kwargs):
        """Initialize the themed console."""
        super().__init__(*args, **kwargs)

    @property
    def theme_obj(self):
        """Get the current theme object, refreshed on each access."""
        return get_theme()

    # Theme color properties
    @property
    def primary(self):
        """Get the primary color from the theme."""
        return self.theme_obj.primary.hex

    @property
    def secondary(self):
        """Get the secondary color from the theme."""
        return self.theme_obj.secondary.hex

    @property
    def accent(self):
        """Get the accent color from the theme."""
        return self.theme_obj.accent.hex

    @property
    def background(self):
        """Get the background color from the theme."""
        return self.theme_obj.background.hex

    @property
    def error(self):
        """Get the error color from the theme."""
        return self.theme_obj.error.hex

    @property
    def warning(self):
        """Get the warning color from the theme."""
        return self.theme_obj.warning.hex

    @property
    def info(self):
        """Get the info color from the theme."""
        return self.theme_obj.info.hex

    @property
    def success(self):
        """Get the success color from the theme."""
        return self.theme_obj.success.hex

    @property
    def text(self):
        """Get the text color from the theme."""
        return self.theme_obj.text.hex

    @property
    def text_muted(self):
        """Get the muted text color from the theme."""
        return self.theme_obj.text_muted.hex

    @property
    def dim(self):
        """Get the dim color from the theme."""
        return self.theme_obj.dim

    @property
    def progress_gradient(self):
        """Get the progress gradient color from the theme."""
        return self.theme_obj.progress_gradient

    @property
    def title_gradient(self):
        """Get the title gradient color from the theme."""
        return self.theme_obj.title_gradient

    @property
    def artist_gradient(self):
        """Get the artist gradient color from the theme."""
        return self.theme_obj.artist_gradient

    @property
    def status_gradient(self):
        """Get the status gradient color from the theme."""
        return self.theme_obj.status_gradient

    @property
    def feedback_gradient(self):
        """Get the feedback gradient color from the theme."""
        return self.theme_obj.feedback_gradient

    @property
    def history_gradient(self):
        """Get the history gradient color from the theme."""
        return self.theme_obj.history_gradient

    def print_styled(
        self, message: str, style_key: str, bold: bool = True, **kwargs
    ) -> None:
        """Print a message with styling from the theme.

        Args:
            message: Text to print
            style_key: Theme attribute to use (e.g., 'primary', 'error')
            bold: Whether to make the text bold
            **kwargs: Additional arguments passed to Console.print
        """
        try:
            color = getattr(self.theme_obj, style_key).hex
            bold_prefix = "bold " if bold else ""
            self.print(f"[{bold_prefix}{color}]{message}[/]", **kwargs)
        except AttributeError:
            logger.warning(f"Unknown style key '{style_key}', using default")
            self.print(message, **kwargs)

    # Specific styling methods using the generic method
    def print_error(self, message: str, **kwargs) -> None:
        """Print an error message with the theme's error color."""
        self.print_styled(message, "error", **kwargs)

    def print_warning(self, message: str, **kwargs) -> None:
        """Print a warning message with the theme's warning color."""
        self.print_styled(message, "warning", **kwargs)

    def print_info(self, message: str, **kwargs) -> None:
        """Print an info message with the theme's info color."""
        self.print_styled(message, "info", bold=False, **kwargs)

    def print_success(self, message: str, **kwargs) -> None:
        """Print a success message with the theme's success color."""
        self.print_styled(message, "success", **kwargs)

    def print_empty(self, message: str, **kwargs) -> None:
        """Print an empty message with the theme's empty color."""
        self.print_styled(message, "warning", **kwargs)

    def style_text(
        self,
        text: str,
        style_key: str,
        text_style: str = None,
        print_it: bool = False,
        **kwargs,
    ) -> str:
        """
        Apply theme styling to text and optionally print it immediately.

        Args:
            text: Text to style
            style_key: Theme attribute to use (e.g., 'primary', 'error')
            text_style: Text style to apply (e.g., 'bold', 'italic')
            print_it: If True, print the styled text immediately
            **kwargs: Additional arguments passed to Console.print() if print_it is True

        Returns:
            Styled text string ready for Rich (always returned even if printed)
        """
        try:
            color = getattr(self.theme_obj, style_key).hex
            style = f"{text_style} " if text_style else ""
            styled_text = f"[{style}{color}]{text}[/]"

            if print_it:
                self.print(styled_text, **kwargs)

            return styled_text

        except AttributeError:
            logger.warning(f"Unknown style key '{style_key}', using default")

            if print_it:
                self.print(text, **kwargs)

            return text

    # Rich component factory methods
    def create_table(
        self,
        title: Optional[str] = None,
        box: Optional[Any] = None,
        border_style: Optional[str] = None,
        **kwargs,
    ) -> Table:
        """
        Create a Rich table with theme-aware styling.

        Args:
            title: Optional title for the table
            box: Box style for the table
            border_style: Border style, uses theme.primary if None
            **kwargs: Additional arguments passed to Table constructor

        Returns:
            Themed Rich Table instance
        """
        from rich.box import ROUNDED

        if box is None:
            box = ROUNDED

        if border_style is None:
            border_style = self.primary

        return Table(title=title, box=box, border_style=border_style, **kwargs)

    def create_panel(
        self,
        renderable: Any,
        title: Optional[str] = None,
        style: Optional[str] = None,
        border_style: Optional[str] = None,
        **kwargs,
    ) -> Panel:
        """
        Create a Rich panel with theme-aware styling.

        Args:
            renderable: Content for the panel
            title: Optional title for the panel
            style: Style for the panel content, uses theme.primary if None
            border_style: Border style, uses theme.secondary if None
            **kwargs: Additional arguments passed to Panel constructor

        Returns:
            Themed Rich Panel instance
        """
        if style is None:
            style = self.primary

        if border_style is None:
            border_style = self.secondary

        return Panel(
            renderable, title=title, style=style, border_style=border_style, **kwargs
        )

    def create_progress(
        self,
        description_style: Optional[str] = None,
        completed_style: Optional[str] = None,
        **kwargs,
    ):
        """
        Create a Rich progress bar with theme-aware styling.

        Args:
            description_style: Style for task description, uses theme.primary if None
            completed_style: Style for completed bar, uses theme.success if None
            **kwargs: Additional arguments passed to Progress constructor

        Returns:
            Themed Rich Progress instance
        """
        if description_style is None:
            description_style = f"bold {self.primary}"

        if completed_style is None:
            completed_style = self.success

        default_columns = kwargs.pop("columns", None)

        # Use theme-aware progress columns if none provided
        if default_columns is None:
            from rich.progress import (
                TextColumn,
                BarColumn,
                TaskProgressColumn,
                TimeRemainingColumn,
            )

            default_columns = [
                TextColumn(f"[{description_style}]{{task.description}}[/]"),
                BarColumn(complete_style=completed_style),
                TaskProgressColumn(),
                TimeRemainingColumn(),
            ]

        from rich.progress import Progress

        return Progress(*default_columns, console=self, **kwargs)

    def create_live_display(
        self, renderable: Any, refresh_per_second: float = 4.0, **kwargs
    ):
        """
        Create a Rich live updating display with theme-aware styling.

        Args:
            renderable: Initial content for the live display
            refresh_per_second: How many times per second to refresh
            **kwargs: Additional arguments passed to Live constructor

        Returns:
            Themed Rich Live instance
        """
        from rich.live import Live

        return Live(
            renderable, console=self, refresh_per_second=refresh_per_second, **kwargs
        )

    def prompt(self, prompt_text: str, style_key: str = "primary", **kwargs) -> str:
        """
        Show a themed prompt for user input.

        Args:
            prompt_text: Text to display in the prompt
            style_key: Theme attribute to use for styling
            **kwargs: Additional arguments passed to Prompt.ask

        Returns:
            User input as a string
        """
        from rich.prompt import Prompt

        try:
            style = getattr(self.theme_obj, style_key).hex
            return Prompt.ask(f"[{style}]{prompt_text}[/]", console=self, **kwargs)
        except AttributeError:
            logger.warning(f"Unknown style key '{style_key}', using default")
            return Prompt.ask(prompt_text, console=self, **kwargs)

    def confirm(self, prompt_text: str, style_key: str = "primary", **kwargs) -> bool:
        """
        Show a themed confirmation prompt for yes/no input.

        Args:
            prompt_text: Text to display in the prompt
            style_key: Theme attribute to use for styling
            **kwargs: Additional arguments passed to Confirm.ask

        Returns:
            True for yes, False for no
        """
        from rich.prompt import Confirm

        try:
            style = getattr(self.theme_obj, style_key).hex
            return Confirm.ask(f"[{style}]{prompt_text}[/]", console=self, **kwargs)
        except AttributeError:
            logger.warning(f"Unknown style key '{style_key}', using default")
            return Confirm.ask(prompt_text, console=self, **kwargs)


def get_console() -> ThemedConsole:
    """
    Get or create a global console instance with the current theme.

    Returns:
        Configured Rich console
    """
    global _console

    # Initialize console with current theme if needed
    if not _console:
        _console = _create_themed_console()

    return _console


def _create_themed_console(theme_name: Optional[str] = None) -> ThemedConsole:
    """
    Create a new Rich console with the specified theme.

    Args:
        theme_name: Name of theme to use, or None for current theme

    Returns:
        New Rich console with the theme applied
    """
    # Get theme from unified theme system
    if theme_name is None:
        theme_name = get_current_theme()

    theme_def = get_theme(theme_name)

    # Convert to Rich theme
    rich_theme = theme_to_rich_theme(theme_def)

    # Create and return the console
    return ThemedConsole(
        theme=rich_theme,
        highlight=True,
        emoji=True,
        width=None,  # Allow automatic width detection
    )


def _update_console_theme(theme_name: Optional[str] = None) -> None:
    """
    Update the global console with a new theme.

    Args:
        theme_name: Name of theme to use, or None for current theme
    """
    global _console
    _console = _create_themed_console(theme_name)


def change_theme(theme_name: str) -> bool:
    """
    Change the application theme and update the console.

    Args:
        theme_name: Name of the theme to switch to

    Returns:
        Success status
    """
    # Update the application theme
    success = set_current_theme(theme_name)
    if success:
        # Update console with new theme
        _update_console_theme(theme_name)
        return True
    return False


# def get_theme(theme_name: str) -> Any:
#     """
#     Get the theme object for a specific theme name.

#     Args:
#         theme_name: Name of the theme to retrieve

#     Returns:
#         Theme object
#     """
#     from aurras.themes import get_theme

#     return get_theme(theme_name)


def get_available_themes() -> list[str]:
    """
    Get a list of all available theme names.

    Returns:
        List of theme names
    """
    from aurras.themes.manager import get_available_themes

    return get_available_themes()


def apply_gradient_to_text(text: str, gradient: list, bold: bool = False) -> str:
    """
    Apply a gradient effect to text using theme colors.

    Args:
        text: The text to apply gradient to
        gradient: List of gradient colors
        bold: Whether to make the text bold

    Returns:
        Rich-formatted text with gradient applied
    """
    if not text or not gradient:
        return text

    if len(text) <= 3:
        bold_prefix = "bold " if bold else ""
        return f"[{bold_prefix}{gradient[0]}]{text}[/{bold_prefix}{gradient[0]}]"

    chars_per_color = max(1, len(text) // len(gradient))
    result = []

    for i, char in enumerate(text):
        color_index = min(i // chars_per_color, len(gradient) - 1)
        color = gradient[color_index]
        bold_prefix = "bold " if bold else ""
        result.append(f"[{bold_prefix}{color}]{char}[/{bold_prefix}{color}]")

    return "".join(result)


# def set_current_theme(theme_name: str) -> bool:
#     """
#     Set the current theme for the application.

#     Args:
#         theme_name: Name of the theme to set

#     Returns:
#         Success status
#     """
#     from aurras.themes import set_current_theme

#     return set_current_theme(theme_name)


# def get_current_theme() -> str:
#     """
#     Get the name of the current theme.

#     Returns:
#         Name of the current theme
#     """
#     from aurras.themes import get_current_theme

#     return get_current_theme()
