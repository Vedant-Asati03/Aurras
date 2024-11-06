import yaml

import path
import default_settings as default_settings_dict


class CreateDefaultSettings:

    def create_dafault_settings(self):
        default_settings = default_settings_dict.default_settings

        with path.settings.open("w") as config_file:
            yaml.dump(default_settings, config_file, default_flow_style=False, indent=4)

    def reset_default_settings(self):
        self.create_dafault_settings()


if __name__ == "__main__":
    CreateDefaultSettings().create_dafault_settings()
