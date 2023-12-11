import yaml
import questionary
from prompt_toolkit import prompt

from config import path
from config.settings.load_default_settings import LoadDefaultSettings


class DisplaySettings(LoadDefaultSettings):
    def __init__(self) -> None:
        super().__init__()
        setting_keys, setting_values = self._retrieve_formatted_settings()
        self.formatted_choices = self._generate_formatted_choices(
            setting_keys, setting_values
        )

    def display_settings(self):
        selected_setting = self._select_setting_from_choices(self.formatted_choices)
        selected_key = list(self.settings)[
            self.formatted_choices.index(selected_setting)
        ]

        UpdateSpecifiedSettings(selected_key).update_specified_setting_through_user()

    def _retrieve_formatted_settings(self):
        keys = list(self.settings)
        values = [
            value if not isinstance(value, dict) else ""
            for value in self.settings.values()
        ]
        return keys, values

    def _generate_formatted_choices(self, keys: list, values: list):
        return [f"{key:<30} {value}" for key, value in zip(keys, values)]

    def _select_setting_from_choices(self, formatted_choices):
        return questionary.select(
            "Select to view or change the setting\n", choices=formatted_choices
        ).ask()


class UpdateSpecifiedSettings(LoadDefaultSettings):
    def __init__(self, setting_to_edit) -> None:
        super().__init__()
        self.user_edit = None
        self.setting_to_edit = setting_to_edit
        self.previous_setting = self.settings[self.setting_to_edit]

    def _get_user_edit(self):
        self.user_edit = (
            prompt(placeholder="write changes", clipboard=True, mouse_support=True)
            .strip()
            .lower()
        )

    def update_specified_setting_through_user(self):
        self._get_user_edit()
        with path.settings.open("w") as config_file:
            self.settings[self.setting_to_edit] = (
                self.user_edit if self.user_edit else self.previous_setting
            )

            yaml.dump(
                self.settings,
                config_file,
                default_flow_style=False,
                indent=4,
            )

    def update_specified_setting_directly(self, updated_setting: str):
        with path.settings.open("w") as config_file:
            self.settings[self.setting_to_edit] = (
                updated_setting if updated_setting else self.previous_setting
            )

            yaml.dump(
                self.settings,
                config_file,
                default_flow_style=False,
                indent=4,
            )
