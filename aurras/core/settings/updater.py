"""
Settings Updater

This module provides functionality for updating specific settings.
"""

from .models import Settings
from .io import load_settings, save_settings


class UpdateSpecifiedSettings:
    """Class for updating specific settings in the settings file."""

    def __init__(self, setting_to_edit) -> None:
        """Initialize with the setting to edit."""
        self.user_edit = None
        self.settings = load_settings()

        # Convert kebab-case to snake_case for the pydantic model
        self.setting_to_edit = setting_to_edit.replace("-", "_")
        self.previous_setting = self._get_nested_attribute(
            self.settings, self.setting_to_edit
        )

    def _get_nested_attribute(self, obj, attr_path):
        """Get attribute that might be nested using dot notation."""
        if "." in attr_path:
            parts = attr_path.split(".")
            current = obj
            for part in parts:
                # Use getattr for pydantic models
                if hasattr(current, part):
                    current = getattr(current, part)
                else:
                    return ""
            return current
        else:
            return getattr(obj, attr_path, "")

    def _set_nested_attribute(self, obj, attr_path, value):
        """Set attribute that might be nested using dot notation."""
        if "." in attr_path:
            parts = attr_path.split(".")
            # We need to handle nested attributes for pydantic models differently
            # This is simplified and may need more robust implementation
            current_dict = obj.dict()
            temp = current_dict
            for i, part in enumerate(parts[:-1]):
                if part not in temp:
                    temp[part] = {}
                if i < len(parts) - 2:
                    temp = temp[part]
            temp[parts[-1]] = value

            # Create new model with updated data
            self.settings = Settings.parse_obj(current_dict)
            return True
        else:
            # For direct attributes, we can use pydantic's __setattr__
            setattr(obj, attr_path, value)
            return True

    def _get_user_edit(self):
        """Get user input for the setting change."""
        # Convert back to kebab-case for user display
        display_setting = self.setting_to_edit.replace("_", "-")
        self.user_edit = (
            input(f"Enter new value for {display_setting}: ").strip().lower()
        )

    def update_specified_setting_through_user(self):
        """Update a specific setting based on user input."""
        self._get_user_edit()
        self.update_specified_setting_directly(self.user_edit)

    def update_specified_setting_directly(self, updated_setting: str):
        """Update a specific setting with the provided value."""
        if not updated_setting:
            updated_setting = self.previous_setting

        self._set_nested_attribute(self.settings, self.setting_to_edit, updated_setting)
        save_settings(self.settings)
