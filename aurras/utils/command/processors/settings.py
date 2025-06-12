"""
Settings command processor for Aurras CLI.

This module handles all settings-related commands and operations.
"""

from typing import Any, Dict, List, Optional, Tuple

from aurras.utils.console import console
from aurras.utils.logger import get_logger
from aurras.utils.decorators import with_error_handling
from aurras.core.settings import SETTINGS, SettingsUpdater

logger = get_logger("aurras.command.processors.settings", log_to_console=False)


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
            styled_category = console.style_text(category, "accent", bold=True)
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

        from aurras.utils.console.renderer import ListDisplay

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

        bullet_color = console.secondary

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
        elif any(
            kw in field_path for kw in ["cache", "log", "buffer", "advanced", "key"]
        ):
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
        """
        Set a specific setting to the provided value.

        Args:
            key: The setting key to update
            value: The new value for the setting

        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        settings_updater = SettingsUpdater(key)
        settings_updater.update_directly(value)

        console.print_success(f"Setting '{key}' updated to '{value}'")
        return 0

    @with_error_handling
    def reset_settings(self) -> int:
        """
        Reset all settings to default values.

        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        from aurras.core.settings import default_settings
        from aurras.core.settings.io import save_settings

        save_settings(default_settings)

        console.print_success("Settings reset to default values")
        return 0

    @with_error_handling
    def toggle_setting(self) -> int:
        """Toggle a yes/no or on/off setting."""
        settings_updater = SettingsUpdater("appearance_settings.display_lyrics")
        current_value = settings_updater.current_value

        new_value = "no" if current_value.lower() == "yes" else "yes"

        if not current_value:
            console.print_error(
                "Setting 'appearance_settings.display_lyrics' not found."
            )
            return 1

        settings_updater.update_directly(new_value)
        console.print_success(f"Lyrics turned {'off' if new_value == 'no' else 'on'}")
        return 0
