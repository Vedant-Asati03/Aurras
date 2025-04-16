"""
Settings command processor for Aurras CLI.

This module handles all settings-related commands and operations.
"""

import os
import logging
from typing import Any, Dict, List, Optional, Tuple

from ...console.manager import get_console
from ...console.renderer import ListDisplay
from ...theme_helper import ThemeHelper, with_error_handling
from ....core.settings.models import Settings
from ....core.settings.io import save_settings
from ....core.settings import load_settings, SettingsUpdater
from ....themes import get_theme, get_current_theme, get_available_themes

logger = logging.getLogger(__name__)

console = get_console()

SETTINGS = load_settings()


class SettingsProcessor:
    """Handle settings-related commands and operations."""

    def __init__(self):
        """Initialize the settings processor."""

    @with_error_handling
    def list_settings(self) -> int:
        """
        List all settings and their current values in a single consolidated table.

        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        schema = SETTINGS.model_json_schema()
        categories = self._build_categories_from_schema(schema)

        all_items: List[Tuple[str, str]] = []

        non_empty_categories = {k: v for k, v in categories.items() if v}
        for category, fields in non_empty_categories.items():
            styled_category = ThemeHelper.get_styled_text(category, "accent", bold=True)
            all_items.append((styled_category, ""))

            for field_path in fields:
                # Get the parent setting name if this is a nested setting
                parts = field_path.split(".")
                parent_path = parts[0] if len(parts) > 1 else None

                # Skip if this is a nested setting and we'll process it with its parent
                if len(parts) > 1 and parent_path in fields:
                    continue

                value = self._get_nested_value(SETTINGS, field_path)
                display_key = field_path.replace("_", "-")

                # Process complex objects (dictionaries, models, etc.)
                if self._is_complex_object(value):
                    # Add the parent setting as a header
                    all_items.append((f"  {display_key}", ""))

                    # Process this complex object's fields
                    nested_items = self._process_complex_object(value, indent_level=4)
                    all_items.extend(nested_items)

                else:
                    # Regular value, just add it directly
                    all_items.append((f"  {display_key}", str(value)))

            # Add a spacer between categories
            if category != list(non_empty_categories.keys())[-1]:
                all_items.append(("", ""))

        list_display = ListDisplay(
            items=all_items,
            title="Aurras Settings",
            description="Use 'aurras settings set <key> <value>' to modify settings\nExample: aurras settings --set appearance-settings.theme ocean",
            show_indices=False,
            use_table=True,
            style_key="settings",
        )

        console.print(list_display.render())
        return 0

    def _is_complex_object(self, value: Any) -> bool:
        """
        Check if a value is a complex object that should be displayed hierarchically.

        Args:
            value: The value to check

        Returns:
            bool: True if the value is a complex object, False otherwise
        """
        # Check if it's a dictionary with content
        if isinstance(value, dict) and value:
            return True

        # Check if it's a Pydantic model or other object with attributes
        if hasattr(value, "__dict__") and not isinstance(
            value, (str, int, float, bool)
        ):
            # Skip objects with no significant attributes
            attrs = {k: v for k, v in vars(value).items() if not k.startswith("_")}
            return bool(attrs)

        return False

    def _process_complex_object(
        self, obj: Any, indent_level: int = 2
    ) -> List[Tuple[str, str]]:
        """
        Process a complex object (dict, model) into list items for display.

        Args:
            obj: The object to process
            indent_level: The current indentation level (spaces)

        Returns:
            List[Tuple[str, str]]: List of (key, value) tuples for display
        """
        items: List[Tuple[str, str]] = []

        # Get theme colors for bullet points
        bullet_color = ThemeHelper.get_theme_color("secondary", "#8BE9FD")

        # Handle dictionary case
        if isinstance(obj, dict):
            for k, v in obj.items():
                # Skip private attributes
                if k.startswith("_"):
                    continue

                display_key = k.replace("_", "-")
                bullet = f"[{bullet_color}][/{bullet_color}]"
                bullet_key = f"{'  ' * (indent_level // 2)}{bullet} {display_key}"

                # Recursively process nested complex objects
                if self._is_complex_object(v):
                    items.append((bullet_key, ""))
                    nested_items = self._process_complex_object(v, indent_level + 2)
                    items.extend(nested_items)
                else:
                    items.append((bullet_key, str(v)))

        # Handle Pydantic model or similar object case
        elif hasattr(obj, "__dict__"):
            # Try different ways to get attributes
            attrs: Dict[str, Any] = {}
            try:
                if hasattr(obj, "model_dump"):
                    attrs = obj.model_dump()  # Pydantic v2
                else:
                    # Regular object
                    attrs = {
                        k: v for k, v in vars(obj).items() if not k.startswith("_")
                    }
            except Exception:
                # Fallback to vars if the above fails
                attrs = {k: v for k, v in vars(obj).items() if not k.startswith("_")}

            # Process each attribute
            for k, v in attrs.items():
                display_key = k.replace("_", "-")
                bullet = f"[{bullet_color}][/{bullet_color}]"
                bullet_key = f"{'  ' * (indent_level // 2)}{bullet} {display_key}"

                # Recursively process nested complex objects
                if self._is_complex_object(v):
                    # For complex nested objects, just show a placeholder or summary
                    if indent_level > 6:  # Limit nesting depth for display
                        items.append((bullet_key, "{...}"))
                    else:
                        items.append((bullet_key, ""))
                        nested_items = self._process_complex_object(v, indent_level + 2)
                        items.extend(nested_items)
                else:
                    items.append((bullet_key, str(v)))

        return items

    def _format_pydantic_object(self, obj: Any) -> str:
        """Format a Pydantic object for display in a concise way."""
        try:
            if hasattr(obj, "model_dump"):
                # Pydantic v2
                obj_dict = obj.model_dump()
            else:
                # Regular object
                obj_dict = vars(obj)

            obj_dict = {k: v for k, v in obj_dict.items() if not k.startswith("_")}

            # Format as concise key-value pairs
            formatted_pairs: List[str] = []
            for k, v in obj_dict.items():
                k_display = k.replace("_", "-")

                if isinstance(v, dict) and v:
                    v_display = "{...}"
                elif hasattr(v, "__dict__") and not isinstance(
                    v, (str, int, float, bool)
                ):
                    v_display = self._format_pydantic_object(v)
                else:
                    v_display = str(v)

                formatted_pairs.append(f"{k_display}='{v_display}'")

            return " ".join(formatted_pairs)

        except Exception:
            return str(obj)

    def _build_categories_from_schema(
        self, schema: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """
        Dynamically build categories dict from schema.

        Args:
            schema: The Pydantic model schema

        Returns:
            Dict[str, List[str]]: Dict of categories to lists of field paths
        """
        categories: Dict[str, List[str]] = {
            "Appearance": [],
            "Playback": [],
            "Authentication": [],
            "Download": [],
            "System": [],
            "Backup": [],
            "Recommendations": [],
            "Advanced": [],
            "Other": [],  # Catch-all for uncategorized settings
        }

        properties = schema.get("properties", {})

        # Map property names to appropriate categories based on naming patterns
        for prop_name, prop_data in properties.items():
            path = prop_name

            # Check if this is a nested object with its own properties
            if prop_data.get("type") == "object" and "properties" in prop_data:
                nested_props = prop_data.get("properties", {})
                for nested_name in nested_props:
                    nested_path = f"{prop_name}.{nested_name}"
                    self._categorize_field(nested_path, categories)
            else:
                self._categorize_field(path, categories)

        return categories

    def _categorize_field(
        self, field_path: str, categories: Dict[str, List[str]]
    ) -> None:
        """Categorize a field path into the appropriate category."""
        if field_path.startswith("appearance_settings"):
            categories["Appearance"].append(field_path)
        elif field_path.startswith("backup.") or "backup" in field_path:
            categories["Backup"].append(field_path)
        elif any(
            kw in field_path for kw in ["volume", "playback", "keyboard_shortcuts"]
        ):
            categories["Playback"].append(field_path)
        elif any(kw in field_path for kw in ["download", "format", "bitrate"]):
            categories["Download"].append(field_path)
        elif any(
            kw in field_path for kw in ["auth", "authentication", "require_", "timeout"]
        ):
            categories["Authentication"].append(field_path)
        elif any(kw in field_path for kw in ["update", "hardware", "media", "system"]):
            categories["System"].append(field_path)
        elif any(kw in field_path for kw in ["recommend", "suggestion"]):
            categories["Recommendations"].append(field_path)
        elif any(kw in field_path for kw in ["cache", "log", "buffer", "advanced"]):
            categories["Advanced"].append(field_path)
        else:
            categories["Other"].append(field_path)

    def _get_nested_value(self, model: Any, dotted_key: str) -> Optional[Any]:
        """Get a nested value from a Pydantic model using dot notation."""
        parts = dotted_key.split(".")
        current = model
        for part in parts:
            if hasattr(current, part):
                current = getattr(current, part)
            else:
                return None
        return current

    @with_error_handling
    def set_setting(self, key: str, value: str) -> int:
        """Set a specific setting to the provided value."""
        settings_updater = SettingsUpdater(key)
        settings_updater.update_directly(value)
        success_color = ThemeHelper.get_theme_color("success", "green")
        console.print(
            f"[bold {success_color}]Updated:[/] Setting '{key}' updated to '{value}'"
        )
        return 0

    @with_error_handling
    def reset_settings(self) -> int:
        """
        Reset all settings to default values.

        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        default_settings = Settings()
        save_settings(default_settings)

        success_color = ThemeHelper.get_theme_color("success", "green")
        console.print(
            f"[bold {success_color}]Reset Complete:[/] All settings have been reset to default values"
        )
        return 0

    @with_error_handling
    def toggle_setting(
        self, setting_name: str, display_name: Optional[str] = None
    ) -> int:
        """Toggle a yes/no or on/off setting."""
        if display_name is None:
            display_name = setting_name.replace("-", " ").title()

        settings_updater = SettingsUpdater(setting_name)
        current_value = settings_updater._get_nested_value(
            settings_updater.SETTINGS, settings_updater.key
        )

        if not current_value:
            error_color = ThemeHelper.get_theme_color("error", "red")
            console.print(
                f"[bold {error_color}]Error:[/] Setting '{setting_name}' not found or has no value"
            )
            return 1

        # Handle different types of toggle settings
        if current_value.lower() in ["yes", "no"]:
            new_value = "no" if current_value.lower() == "yes" else "yes"
            status = "ON" if new_value == "yes" else "OFF"
        elif current_value.lower() in ["on", "off"]:
            new_value = "off" if current_value.lower() == "on" else "on"
            status = "ON" if new_value == "on" else "OFF"
        else:
            new_value = "off" if current_value.lower() != "off" else "on"
            status = "ON" if new_value != "off" else "OFF"

        settings_updater.update_directly(new_value)
        success_color = ThemeHelper.get_theme_color("success", "green")
        console.print(
            f"[bold {success_color}]Setting Updated:[/] {display_name} turned {status}"
        )
        return 0

    @with_error_handling
    def set_download_path(self, path: str) -> int:
        """Set the download path to the provided directory."""
        expanded_path = os.path.expanduser(path)

        warning_color = ThemeHelper.get_theme_color("warning", "yellow")

        # Check if path exists
        if not os.path.exists(expanded_path):
            create_dir = console.input(
                f"[{warning_color}]Path '{expanded_path}' does not exist. Create it? (y/n): [/]"
            )
            if create_dir.lower() == "y":
                os.makedirs(expanded_path, exist_ok=True)
            else:
                console.print(
                    f"[{warning_color}]Cancelled:[/] Operation cancelled by user"
                )
                return 1

        settings_updater = SettingsUpdater("download_path")
        settings_updater.update_directly(expanded_path)

        success_color = ThemeHelper.get_theme_color("success", "green")
        console.print(
            f"[bold {success_color}]Path Updated:[/] Download path set to: {expanded_path}"
        )
        return 0

    @with_error_handling
    def list_themes(self) -> int:
        """List all available themes with the current theme highlighted."""
        available_themes = get_available_themes()
        current_theme_name = get_current_theme()

        items: List[Tuple[str, str]] = []
        for theme_name in available_themes:
            theme = get_theme(theme_name)
            description = theme.display_name if hasattr(theme, "display_name") else ""
            items.append((theme_name, description))

        try:
            selected_index = available_themes.index(current_theme_name)
        except ValueError:
            selected_index = -1

        theme_list = ListDisplay(
            items,
            title=ThemeHelper.get_styled_text("Available Themes", "header", bold=True),
            description=f"Current theme: {ThemeHelper.get_styled_text(current_theme_name, 'accent')}",
            selected_index=selected_index,
            show_indices=True,
            style_key="list",
            highlight_style="accent",
        )

        console.print(theme_list.render())
        return 0

    @with_error_handling
    def set_theme(self, theme_name: str) -> int:
        """Set the theme to the specified name."""
        from ..processors.theme import ThemeProcessor

        theme_processor = ThemeProcessor()
        return theme_processor.set_theme(theme_name)

    @with_error_handling
    def open_settings_ui(self) -> int:
        """Open the settings management UI."""
        from ....ui.command_palette import DisplaySettings

        settings_ui = DisplaySettings()
        settings_ui.display_settings()
        return 0

    def _display_error(self, message: str) -> None:
        """Display an error message to the console."""
        error_color = ThemeHelper.get_theme_color("error", "red")
        console.print(f"[bold {error_color}]Error:[/] {message}")


# Instantiate processor for direct import
processor = SettingsProcessor()
