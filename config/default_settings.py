import yaml
import config.config as path


class CreateDefaultSettings:
    def __init__(self) -> None:
        self.default_settings = {
            "max_volume": "130",
            "show_video": "false",
            "show_lyrics": "true",
            "authenticated": "true",
            "keyboard_shortcuts": {
                "end_song": "q",
                "pause": "p",
                "translate_lyrics": "t",
            },
        }

    def create_dafault_settings(self):
        with path.default_settings.open("w") as config_file:
            yaml.dump(
                self.default_settings, config_file, default_flow_style=False, indent=4
            )

    def reset_default_settings(self):
        self.create_dafault_settings()


if __name__ == "__main__":
    CreateDefaultSettings().create_dafault_settings()
