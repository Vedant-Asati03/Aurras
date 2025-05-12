"""
Settings Updater

This module provides functionality for updating specific settings using dot notation.
"""

from aurras.core.settings.io import save_settings
from aurras.core.settings import Settings, SETTINGS


class SettingsUpdater:
    """Class for updating specific settings using dot notation."""

    def __init__(self, key_to_update: str) -> None:
        self.key = key_to_update.replace("-", "_")  # support kebab-case
        self.current_value = self._get_nested_value(SETTINGS, self.key)
        self.new_value = None

    def _get_nested_value(self, model, dotted_key: str):
        """Get a nested value from a Pydantic model using dot notation."""
        parts = dotted_key.split(".")
        current = model
        for part in parts:
            if hasattr(current, part):
                current = getattr(current, part)
            else:
                return None
        return current

    def _set_nested_value(self, model, dotted_key: str, value):
        """Set a nested value in a Pydantic model using dot notation."""
        data = model.model_dump()
        parts = dotted_key.split(".")
        temp = data

        for part in parts[:-1]:
            if part not in temp or not isinstance(temp[part], dict):
                temp[part] = {}
            temp = temp[part]

        temp[parts[-1]] = value

        # Rebuild model with updated data
        return Settings(**data)

    def _prompt_user_input(self):
        """Prompt the user for the new value."""
        display_key = self.key.replace("_", "-")
        self.new_value = input(f"Enter new value for '{display_key}': ").strip()

    def update_via_user_input(self):
        """Main interface: prompt and update."""
        self._prompt_user_input()
        self.apply_update()

    def update_directly(self, value: str):
        """Set the new value programmatically."""
        self.new_value = value
        self.apply_update()

    def apply_update(self):
        """Apply the update and save the settings."""
        global SETTINGS
        SETTINGS = self._set_nested_value(SETTINGS, self.key, self.new_value)
        save_settings(SETTINGS)
