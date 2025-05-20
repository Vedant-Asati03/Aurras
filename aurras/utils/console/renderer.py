"""
Console UI renderer components for rich terminal interfaces.

This module provides a component-based architecture for building
rich terminal user interfaces with consistent styling and behavior.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable, Union, Tuple

from aurras.utils.logger import get_logger
from aurras.utils.exceptions import DisplayError, ThemeError
from aurras.utils.console import console, apply_gradient_to_text

logger = get_logger("aurras.ui.renderer", log_to_console=False)


class UIComponent(ABC):
    """Base class for UI components in the console renderer."""

    @abstractmethod
    def render(self) -> Any:
        """Render the component to a Rich renderable object."""
        pass


class UIRenderer:
    """Component-based UI renderer for the console."""

    def __init__(self):
        """
        Initialize the UI renderer.

        Args:
            console: Rich console to use for rendering
        """
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
            # Use the new console factory method
            self._live = console.create_live_display(
                self._generate_live_render(),
                refresh_per_second=refresh_per_second,
                transient=True,
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
                message = console.style_text(
                    text="No UI components registered", style_key="info"
                )
                return message

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
                    console.print(layout_func())
                except ThemeError as e:
                    error_msg = console.style_text(
                        text=f"Theme error in layout function: {e}",
                        style_key="error",
                        print_it=True,
                    )
                    logger.error(error_msg)
                except Exception as e:
                    error_msg = console.style_text(
                        text=f"Error in layout function: {e}",
                        style_key="error",
                        print_it=True,
                    )
                    logger.error(error_msg)
            else:
                # Default layout - just print components in order
                for name, component in self.components.items():
                    try:
                        rendered = component.render()
                        if rendered is not None:
                            console.print(rendered)
                    except ThemeError as e:
                        error_msg = console.style_text(
                            text=f"Theme error rendering component {name}: {e}",
                            style_key="error",
                            print_it=True,
                        )
                        logger.error(error_msg)
                    except Exception as e:
                        error_msg = console.style_text(
                            text=f"Error rendering component {name}: {e}",
                            style_key="error",
                            print_it=True,
                        )
                        logger.error(error_msg)
        except Exception as e:
            error_msg = f"Critical error in rendering: {e}"
            logger.error(error_msg)
            raise DisplayError(error_msg) from e


class Header(UIComponent):
    """Header component with title and subtitle."""

    def __init__(
        self,
        title: str,
        subtitle: str = "",
        style: str = "bold",
    ):
        """
        Initialize the header component.

        Args:
            title: Main title text
            subtitle: Optional subtitle text
            style: Style for the title
        """
        self.title = title
        self.subtitle = subtitle
        self.style = style

    def render(self) -> str:
        """Render the header with appropriate styling."""
        if self.subtitle:
            title = console.style_text(text=self.title, style_key="primary", bold=True)
            subtitle = console.style_text(text=self.subtitle, style_key="text_muted")
            result = f"{title}\n{subtitle}"
        else:
            result = console.style_text(text=self.title, style_key="primary", bold=True)

        return result


class ProgressIndicator(UIComponent):
    """
    Enhanced progress indicator with description and time display.
    """

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

        values_color = console.text_muted

        filled_bar = console.style_text(
            text=apply_gradient_to_text(
                f"{'█' * filled_width}", console.progress_gradient
            ),
            style_key="primary",
        )
        unfilled_bar = console.style_text(
            text=f"{'█' * unfilled_width}", style_key="text_muted"
        )
        bar = f"{filled_bar}{unfilled_bar}"

        if self.unit == "s":
            from .formatting import format_time_values

            completed_fmt = format_time_values(self.completed)
            total_fmt = format_time_values(self.total)
            values_text = (
                f"[{values_color}]{completed_fmt} / [{values_color}]{total_fmt}[/]"
            )
        else:
            values_text = f"[{values_color}]{self.completed:.1f}[/] / [{values_color}]{self.total:.1f}{self.unit}[/]"

        if self.description:
            desc_text = console.style_text(
                text=f"{self.description} ", style_key="text_muted", text_style="bold"
            )
        else:
            desc_text = ""

        return f"{desc_text}{bar} {values_text}"


class FeedbackMessage(UIComponent):
    """Component for displaying user feedback and notifications."""

    def __init__(
        self,
        message: str,
        action: str = "",
        style: str = "feedback",
        timeout: float = 1.5,  # Default timeout of 5 seconds
        created_at: float = None,
    ):
        """
        Initialize feedback message.

        Args:
            message: Main message text
            action: Optional action text
            style: Style key (feedback, error, system)
            timeout: Number of seconds to display the message (0 = never expire)
            created_at: Timestamp when the message was created (default: current time)
        """
        import time

        self.message = message
        self.action = action
        self.style = style
        self.timeout = timeout
        self.created_at = created_at or time.time()

    def is_expired(self) -> bool:
        """
        Check if the feedback message has expired based on timeout.

        Returns:
            True if message should no longer be displayed, False otherwise
        """
        if self.timeout <= 0:
            return False  # Messages with timeout <= 0 never expire

        import time

        current_time = time.time()
        return (current_time - self.created_at) > self.timeout

    def render(self) -> str:
        """Render the feedback message with appropriate styling."""
        match self.style:
            case "error":
                color = console.error
                icon = f"[bold {color}][/]"
            case "system":
                color = console.info
                icon = f"[bold {color}][/]"
            case _:
                color = console.success
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

        if binding_count == 0:
            no_bindings_msg = console.style_text(
                text="No keyboard shortcuts available", style_key="text_muted"
            )
            return no_bindings_msg

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
                stlyed_key = console.style_text(
                    text=key, style_key=self.key_style, text_style="bold"
                )
                styled_desc = console.style_text(text=desc, style_key=self.value_style)
                column_text.append(f"{stlyed_key} {styled_desc}")

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
        show_header: bool = True,
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
        self.show_header = show_header
        self.max_height = max_height
        self.style_key = style_key
        self.use_table = use_table

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
        item_style = console.text
        description_style = console.text_muted
        highlight_color = console.accent
        # border_style = console.primary

        if not self.items:
            empty_msg = console.style_text(
                text="No items to display", style_key="text_muted", text_style="italic"
            )

            if self.use_table:
                table = console.create_table(
                    title=self.title if self.title else "Empty List"
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
            table = console.create_table(
                title=self.title if self.title else None,
                caption=self._get_pagination_text() if self.page_count > 1 else None,
                show_header=self.show_header,
            )

            # Configure columns
            if self.show_indices:
                table.add_column("", style="dim", width=3, justify="right")

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
                lines.append(f"[bold {console.theme_obj.primary.hex}]{self.title}[/]")
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
                    index_prefix = f"{actual_idx + 1}. " if self.show_indices else " "
                    lines.append(f"[{style_prefix}]{index_prefix}{name}[/]")

            # Add pagination info if applicable
            if self.page_count > 1:
                lines.append("")
                lines.append(self._get_pagination_text())

            return "\n".join(lines)

    def _get_pagination_text(self) -> str:
        """Get pagination status text."""
        return f"[{console.theme_obj.dim}]Page {self.current_page + 1} of {self.page_count} ({len(self.items)} items)[/]"

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
