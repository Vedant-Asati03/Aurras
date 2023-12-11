import yaml

from config import path


class LoadDefaultSettings:
    def __init__(self) -> None:
        self.settings = self.load_default_settings()

    def load_default_settings(self):
        with path.settings.open("r") as default_settings:
            settings = yaml.safe_load(default_settings)

        return settings
