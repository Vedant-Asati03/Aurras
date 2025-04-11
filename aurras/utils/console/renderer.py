"""
Console UI renderer components for rich terminal interfaces.

This module provides a component-based architecture for building
rich terminal user interfaces with consistent styling and behavior.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable, Union
from rich.console import Console
from rich.style import Style

from ..console.manager import get_console
from ...themes import get_theme, get_current_theme, ThemeDefinition
from ...themes.adapters import theme_to_rich_theme, get_gradient_styles

logger = logging.getLogger(__name__)


def get_current_theme_instance() -> ThemeDefinition:
    """
    Get the current theme instance.

    Returns:
        The current theme definition
    """
    theme_name = get_current_theme()
    return get_theme(theme_name)


def get_theme_styles(theme_obj: ThemeDefinition) -> Dict[str, Union[Style, str]]:
    """
    Get Rich compatible styles from a theme object.

    Args:
        theme_obj: Theme definition object

    Returns:
        Dictionary of style names to Rich Style objects
    """
    rich_theme = theme_to_rich_theme(theme_obj)
    return rich_theme.styles


def get_theme_gradients(theme_obj: ThemeDefinition) -> Dict[str, List[str]]:
    """
    Get gradient styles from a theme object.

    Args:
        theme_obj: Theme definition object

    Returns:
        Dictionary of gradient names to lists of color strings
    """
    return get_gradient_styles(theme_obj)


# Get the current theme for convenient access
theme = get_current_theme_instance()


class UIComponent(ABC):
    """Base class for UI components in the console renderer."""

    @abstractmethod
    def render(self) -> Any:
        """Render the component to a Rich renderable object."""
        pass


class UIRenderer:
    """Component-based UI renderer for the console."""

    def __init__(self, console: Optional[Console] = None):
        """
        Initialize the UI renderer.

        Args:
            console: Rich console to use for rendering
        """
        self.console = console or get_console()
        self.components: Dict[str, UIComponent] = {}

    def add_component(self, name: str, component: UIComponent) -> None:
        """
        Add a component to the renderer.

        Args:
            name: Unique name for the component
            component: UIComponent instance
        """
        self.components[name] = component

    def remove_component(self, name: str) -> None:
        """
        Remove a component from the renderer.

        Args:
            name: Name of the component to remove
        """
        if name in self.components:
            del self.components[name]

    def render(self, layout_func: Optional[Callable] = None) -> None:
        """
        Render all components to the console.

        Args:
            layout_func: Optional function to layout the components
        """
        if layout_func:
            self.console.print(layout_func())
        else:
            # Default layout - just print components in order
            for name, component in self.components.items():
                try:
                    rendered = component.render()
                    if rendered is not None:
                        self.console.print(rendered)
                except Exception as e:
                    logger.error(f"Error rendering component {name}: {e}")
                    self.console.print(f"[bold red]Error rendering {name}[/]")


class Header(UIComponent):
    """Header component with title and subtitle."""

    def __init__(
        self, title: str, subtitle: str = "", style: str = "bold", box_style=None
    ):
        """
        Initialize the header component.

        Args:
            title: Main title text
            subtitle: Optional subtitle text
            style: Style for the title
            box_style: Optional box style for panels
        """
        self.title = title
        self.subtitle = subtitle
        self.style = style
        self.box_style = box_style

    def render(self) -> str:
        """Render the header with appropriate styling."""
        theme_obj = get_current_theme_instance()
        theme_styles = get_theme_styles(theme_obj)

        header_color = theme_styles.get(
            "header", theme_styles.get("primary", "#FFFFFF")
        )
        subtitle_color = theme_styles.get("text_muted", "dim")

        # Create title with styling
        styled_title = f"[{self.style} {header_color}]{self.title}[/]"

        # Add subtitle if provided
        if self.subtitle:
            result = f"{styled_title}\n[{subtitle_color}]{self.subtitle}[/]"
        else:
            result = styled_title

        return result


class ProgressIndicator(UIComponent):
    """Enhanced progress indicator with description and time display."""

    def __init__(
        self,
        total: float,
        completed: float,
        description: str = "",
        unit: str = "",
        bar_width: int = 40,
    ):
        """
        Initialize progress indicator.

        Args:
            total: Total value (100%)
            completed: Current completed value
            description: Description text
            unit: Unit label for values
            bar_width: Width of progress bar in characters
        """
        self.total = max(0.1, total)  # Avoid division by zero
        self.completed = max(0, min(completed, self.total))
        self.description = description
        self.unit = unit
        self.bar_width = bar_width

    def render(self) -> str:
        """Render the progress bar with time indicators."""
        progress = min(100, int((self.completed / self.total) * 100))

        filled_width = int((progress / 100) * self.bar_width)
        unfilled_width = self.bar_width - filled_width

        # Get colors from the theme using adapter helpers
        theme_obj = get_current_theme_instance()
        theme_styles = get_theme_styles(theme_obj)
        theme_gradients = get_theme_gradients(theme_obj)

        color = theme_styles.get("accent", "#BD93F9")
        values_color = theme_styles.get("text_muted", "#CCCCCC")
        percentage_color = theme_styles.get("accent", "#BD93F9")

        # Get progress gradient if available
        progress_colors = theme_gradients.get("progress", [color])
        if len(progress_colors) > 0:
            color = progress_colors[0]

        bar = f"[{color}]{'▓' * filled_width}[/][dim]{'░' * unfilled_width}[/]"

        if self.unit == "s":
            from .formatting import format_time_values

            completed_fmt = format_time_values(self.completed)
            total_fmt = format_time_values(self.total)
            values_text = f"[dim {values_color}]{completed_fmt}[/] / [dim {values_color}]{total_fmt}[/]"
        else:
            values_text = f"[dim {values_color}]{self.completed:.1f}[/] / [dim {values_color}]{self.total:.1f}{self.unit}[/]"

        if self.description:
            desc_text = f"[bold]{self.description}[/] "
        else:
            desc_text = ""

        return f"{desc_text}{bar} [bold {percentage_color}][/] {values_text}"


class FeedbackMessage(UIComponent):
    """Component for displaying user feedback and notifications."""

    def __init__(
        self,
        message: str,
        action: str = "",
        style: str = "feedback",
    ):
        """
        Initialize feedback message.

        Args:
            message: Main message text
            action: Optional action text
            style: Style key (feedback, error, system)
        """
        self.message = message
        self.action = action
        self.style = style

    def render(self) -> str:
        """Render the feedback message with appropriate styling."""
        theme_obj = get_current_theme_instance()
        theme_styles = get_theme_styles(theme_obj)
        theme_gradients = get_theme_gradients(theme_obj)

        match self.style:
            case "error":
                color = theme_styles.get("error", "#FF5555")
                icon = f"[bold {color}][/]"
            case "system":
                color = theme_styles.get("info", theme_styles.get("accent", "#33CCFF"))
                icon = f"[bold {color}][/]"
            case _:
                # Try to use feedback gradient if available
                feedback_colors = theme_gradients.get("feedback", [])
                if feedback_colors:
                    color = feedback_colors[0]
                else:
                    color = theme_styles.get("success", "#50FA7B")
                icon = f"[bold {color}][/]"

        if self.action:
            return f"{icon} [bold {color}]{self.action}:[/] {self.message}"
        else:
            return f"{icon} {self.message}"


class KeybindingHelp(UIComponent):
    """Component for displaying keyboard shortcuts and controls."""

    def __init__(
        self,
        keybindings: Dict[str, str],
        columns: int = 2,
        key_style: str = None,
        value_style: str = None,
    ):
        """
        Initialize keybinding help component.

        Args:
            keybindings: Dict of key -> description mappings
            columns: Number of columns for display
            key_style: Custom style for key text
            value_style: Custom style for value text
        """
        self.keybindings = keybindings
        self.columns = columns
        self.key_style = key_style
        self.value_style = value_style

    def render(self) -> str:
        """Render the keybindings in multiple columns."""
        binding_count = len(self.keybindings)

        # Get theme styles using adapter helpers
        theme_obj = get_current_theme_instance()
        theme_styles = get_theme_styles(theme_obj)

        # Use provided styles or fall back to theme defaults
        key_style = self.key_style or theme_styles.get("accent", "#BD93F9")
        value_style = self.value_style or theme_styles.get("text", "white")

        if binding_count == 0:
            return (
                f"[{theme_styles.get('dim', 'dim')}]No keyboard shortcuts available[/]"
            )

        items_per_col = (binding_count + self.columns - 1) // self.columns

        columns_text = []
        items = list(self.keybindings.items())

        for i in range(self.columns):
            start = i * items_per_col
            end = min(start + items_per_col, binding_count)

            if start >= binding_count:
                break

            column_text = []
            for key, desc in items[start:end]:
                column_text.append(
                    f"[bold {key_style}]{key}[/] [{value_style}]{desc}[/]"
                )

            columns_text.append(" · ".join(column_text))

        return " · ".join(columns_text)
