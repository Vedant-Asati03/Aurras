"""
Console UI renderer components for rich terminal interfaces.

This module provides a component-based architecture for building
rich terminal user interfaces with consistent styling and behavior.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable, Union, Tuple

from rich.live import Live
from rich.style import Style
from rich.table import Table
from rich.box import ROUNDED
from rich.console import Console

from ..console.manager import get_console
from ...utils.exceptions import DisplayError, ThemeError
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
        self._live = None
        self._running = False
        self._layout_func = None

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

    def start_live_display(
        self, refresh_per_second: float = 4.0, layout_func: Optional[Callable] = None
    ) -> None:
        """
        Start a live-updating display.

        Args:
            refresh_per_second: How many times per second to refresh the display
            layout_func: Optional function to create the layout

        Raises:
            DisplayError: If there's an issue with starting the live display
        """
        if self._running:
            return

        self._layout_func = layout_func

        try:
            self._live = Live(
                self._generate_live_render(),
                console=self.console,
                refresh_per_second=refresh_per_second,
            )

            self._live.start()
            self._running = True
            logger.info("Live display started successfully")

        except Exception as e:
            error_msg = f"Failed to start live display: {e}"
            logger.error(error_msg)
            self.render(layout_func)
            raise DisplayError(error_msg) from e

    def stop_live_display(self) -> None:
        """
        Stop the live display.

        Raises:
            DisplayError: If there's an issue with stopping the live display
        """
        if not self._live and self._running:
            # Just to make sure states are consistent
            self._running = False
            self._live = None
            return

        try:
            self._live.stop()
            logger.info("Live display stopped")

        except Exception as e:
            error_msg = f"Error stopping live display: {e}"
            logger.error(error_msg)
            raise DisplayError(error_msg) from e

        finally:
            self._running = False
            self._live = None

    def _generate_live_render(self) -> Any:
        """
        Internal render function for live display.

        Returns:
            A Rich-compatible renderable

        Raises:
            DisplayError: For critical rendering errors
            ThemeError: For theme-related rendering errors
        """
        try:
            if self._layout_func:
                try:
                    return self._layout_func()
                except ThemeError as e:
                    logger.error(f"Theme error in layout function: {e}")
                    return (
                        f"[bold red]Theme error in layout function: {str(e)}[/bold red]"
                    )
                except Exception as e:
                    logger.error(f"Error in layout function: {e}")
                    return f"[bold red]Error in layout function: {str(e)}[/bold red]"

            rendered_components = []
            if not self.components:
                return "[yellow]No UI components registered[/yellow]"

            for name, component in self.components.items():
                try:
                    rendered = component.render()
                    if rendered is not None:
                        rendered_components.append(rendered)
                except ThemeError as e:
                    error_msg = f"Theme error rendering component {name}: {e}"
                    logger.error(error_msg)
                    rendered_components.append(f"[bold red]{error_msg}[/bold red]")
                except Exception as e:
                    error_msg = f"Error rendering component {name}: {e}"
                    logger.error(error_msg)
                    rendered_components.append(f"[bold red]{error_msg}[/bold red]")

            if not rendered_components:
                return "[yellow]No renderable content[/yellow]"

            from rich.console import Group

            return Group(*rendered_components)

        except Exception as e:
            error_msg = f"Critical error in live rendering: {e}"
            logger.error(error_msg)
            raise DisplayError(error_msg) from e

    def refresh(self) -> None:
        """
        Force a refresh of the live display.

        Raises:
            DisplayError: If there's a critical error refreshing the display
        """
        if self._live and self._running:
            try:
                self._live.update(self._generate_live_render())

            except ThemeError as e:
                logger.error(f"Theme error while refreshing display: {e}")

            except Exception as e:
                error_msg = f"Error refreshing live display: {e}"
                logger.error(error_msg)
                raise DisplayError(error_msg) from e

    def render(self, layout_func: Optional[Callable] = None) -> None:
        """
        Render all components to the console.

        Args:
            layout_func: Optional function to layout the components

        Raises:
            DisplayError: For critical display errors
            ThemeError: For theme-related errors
        """
        try:
            if layout_func:
                try:
                    self.console.print(layout_func())
                except ThemeError as e:
                    error_msg = f"Theme error in layout function: {e}"
                    logger.error(error_msg)
                    self.console.print(f"[bold red]{error_msg}[/]")
                except Exception as e:
                    error_msg = f"Error in layout function: {e}"
                    logger.error(error_msg)
                    self.console.print(f"[bold red]{error_msg}[/]")
            else:
                # Default layout - just print components in order
                for name, component in self.components.items():
                    try:
                        rendered = component.render()
                        if rendered is not None:
                            self.console.print(rendered)
                    except ThemeError as e:
                        error_msg = f"Theme error rendering component {name}: {e}"
                        logger.error(error_msg)
                        self.console.print(f"[bold red]{error_msg}[/]")
                    except Exception as e:
                        error_msg = f"Error rendering component {name}: {e}"
                        logger.error(error_msg)
                        self.console.print(f"[bold red]{error_msg}[/]")
        except Exception as e:
            error_msg = f"Critical error in rendering: {e}"
            logger.error(error_msg)
            raise DisplayError(error_msg) from e


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


class ListDisplay(UIComponent):
    """Component for displaying lists of items with consistent styling."""

    def __init__(
        self,
        items: List[Union[str, Tuple[str, str]]],
        title: str = None,
        description: str = None,
        selected_index: int = -1,
        show_indices: bool = False,
        max_height: int = None,
        style_key: str = "list",
        use_table: bool = True,
        highlight_style: str = None,
    ):
        """
        Initialize a list display component.

        Args:
            items: List of strings or (name, description) tuples to display
            title: Optional title for the list
            description: Optional description text
            selected_index: Index of the currently selected item (-1 for none)
            show_indices: Whether to show numerical indices
            max_height: Maximum number of items to show at once
            style_key: Theme style key to use for formatting
            use_table: Whether to use a table for formatting (False for simple list)
            highlight_style: Style to use for highlighting the selected item
        """
        self.items = items
        self.title = title
        self.description = description
        self.selected_index = selected_index
        self.show_indices = show_indices
        self.max_height = max_height
        self.style_key = style_key
        self.use_table = use_table
        self.highlight_style = highlight_style

        # Calculate pagination values if max_height is set
        self.page_count = 1
        self.current_page = 0

        if max_height and len(items) > max_height:
            self.page_count = (len(items) + max_height - 1) // max_height
            if selected_index >= 0:
                self.current_page = min(
                    selected_index // max_height, self.page_count - 1
                )

    def render(self) -> Any:
        """Render the list with appropriate styling."""
        # Get theme styles
        theme_obj = get_current_theme_instance()
        theme_styles = get_theme_styles(theme_obj)
        theme_gradients = get_theme_gradients(theme_obj)

        # Get style colors from theme
        title_style = theme_styles.get("header", theme_styles.get("primary", "#FFFFFF"))
        item_style = theme_styles.get(
            self.style_key, theme_styles.get("text", "#CCCCCC")
        )
        description_style = theme_styles.get("text_muted", "dim")

        # Properly resolve highlight style color - this is where the bug was
        if self.highlight_style:
            # If highlight_style is a theme key, look it up in theme_styles
            highlight_color = theme_styles.get(
                self.highlight_style, self.highlight_style
            )
        else:
            # Default fallback is the accent color from theme
            highlight_color = theme_styles.get("accent", "#BD93F9")

        border_style = theme_styles.get("border", theme_styles.get("primary", "cyan"))

        # Handle empty list
        if not self.items:
            empty_msg = "[italic]No items to display[/]"
            if self.use_table:
                table = Table(
                    box=ROUNDED,
                    border_style=border_style,
                    title=self.title if self.title else "Empty List",
                )
                table.add_column("Message")
                table.add_row(empty_msg)
                return table
            else:
                return f"{empty_msg}"

        # Apply pagination if needed
        visible_items = self.items
        if self.max_height and len(self.items) > self.max_height:
            start_idx = self.current_page * self.max_height
            end_idx = min(start_idx + self.max_height, len(self.items))
            visible_items = self.items[start_idx:end_idx]

        # Render as table if requested
        if self.use_table:
            table = Table(
                box=ROUNDED,
                border_style=border_style,
                title=self.title if self.title else None,
                caption=self._get_pagination_text() if self.page_count > 1 else None,
            )

            # Configure columns
            if self.show_indices:
                table.add_column("#", style="dim", width=3, justify="right")

            has_descriptions = any(
                isinstance(item, tuple) and len(item) > 1 for item in self.items
            )

            table.add_column("Name", style=item_style)
            if has_descriptions:
                table.add_column("Description", style=description_style)

            # Add rows
            for i, item in enumerate(visible_items):
                start_idx = self.current_page * (self.max_height or 0)
                actual_idx = start_idx + i

                # Determine if this row should be highlighted
                is_selected = actual_idx == self.selected_index
                row_style = f"bold {highlight_color}" if is_selected else None

                if isinstance(item, tuple) and len(item) > 1:
                    name, desc = item[0], item[1]

                    if self.show_indices:
                        table.add_row(str(actual_idx + 1), name, desc, style=row_style)
                    else:
                        table.add_row(name, desc, style=row_style)
                else:
                    name = item

                    if self.show_indices:
                        table.add_row(str(actual_idx + 1), name, style=row_style)
                    else:
                        table.add_row(name, style=row_style)

            # Add description as caption if provided
            if self.description:
                if table.caption:
                    table.caption = f"{table.caption}\n{self.description}"
                else:
                    table.caption = self.description

            return table

        # Simple list rendering (not using table)
        else:
            lines = []

            # Add title if provided
            if self.title:
                lines.append(f"[bold {title_style}]{self.title}[/]")
                lines.append("")

            # Add description if provided
            if self.description:
                lines.append(f"[{description_style}]{self.description}[/]")
                lines.append("")

            # Add items
            for i, item in enumerate(visible_items):
                start_idx = self.current_page * (self.max_height or 0)
                actual_idx = start_idx + i

                # Determine if this item should be highlighted
                style_prefix = (
                    f"bold {highlight_color}"
                    if actual_idx == self.selected_index
                    else item_style
                )

                if isinstance(item, tuple) and len(item) > 1:
                    name, desc = item[0], item[1]
                    index_prefix = f"{actual_idx + 1}. " if self.show_indices else ""
                    lines.append(
                        f"[{style_prefix}]{index_prefix}{name}[/] - [{description_style}]{desc}[/]"
                    )
                else:
                    name = item
                    index_prefix = f"{actual_idx + 1}. " if self.show_indices else "• "
                    lines.append(f"[{style_prefix}]{index_prefix}{name}[/]")

            # Add pagination info if applicable
            if self.page_count > 1:
                lines.append("")
                lines.append(self._get_pagination_text())

            return "\n".join(lines)

    def _get_pagination_text(self) -> str:
        """Get pagination status text."""
        theme_obj = get_current_theme_instance()
        theme_styles = get_theme_styles(theme_obj)
        dim_style = theme_styles.get("dim", "dim")

        return f"[{dim_style}]Page {self.current_page + 1} of {self.page_count} ({len(self.items)} items)[/]"

    def next_page(self) -> bool:
        """
        Move to the next page if available.

        Returns:
            True if page changed, False otherwise
        """
        if self.current_page < self.page_count - 1:
            self.current_page += 1
            return True
        return False

    def prev_page(self) -> bool:
        """
        Move to the previous page if available.

        Returns:
            True if page changed, False otherwise
        """
        if self.current_page > 0:
            self.current_page -= 1
            return True
        return False

    def select_item(self, index: int) -> bool:
        """
        Select an item by index.

        Args:
            index: Index of the item to select

        Returns:
            True if selection changed, False otherwise
        """
        if 0 <= index < len(self.items):
            self.selected_index = index

            # Update current page if needed to show the selected item
            if self.max_height:
                new_page = index // self.max_height
                if new_page != self.current_page:
                    self.current_page = new_page

            return True
        return False

    def get_selected_item(self) -> Optional[Union[str, Tuple[str, str]]]:
        """
        Get the currently selected item.

        Returns:
            The selected item, or None if nothing is selected
        """
        if 0 <= self.selected_index < len(self.items):
            return self.items[self.selected_index]
        return None
