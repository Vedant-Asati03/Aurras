"""
Theme command processor for Aurras CLI.

Handles listing, setting, cycling, and saving UI themes.
"""

from aurras.utils.console import console
from aurras.utils.logger import get_logger
from aurras.utils.console.manager import (
    get_theme,
    get_available_themes,
    get_current_theme,
    set_current_theme,
)

logger = get_logger("aurras.command.processors.theme", log_to_console=False)


class ThemeProcessor:
    """Handles theme-related commands and settings updates."""

    def _persist_theme(self, theme_name: str) -> bool:
        """Persist selected theme to settings."""
        try:
            from aurras.core.settings.updater import SettingsUpdater

            updater = SettingsUpdater("appearance_settings.theme")
            updater.update_directly(theme_name)
            logger.info(f"Theme {theme_name} persisted successfully in settings")
            return True
        except Exception as e:
            logger.error(f"Failed to persist theme: {e}")
            return False

    def display_current_theme(self) -> int:
        """Display the current theme."""
        try:
            current_theme = get_current_theme()
            theme = get_theme(current_theme)

            console.style_text(
                text=f"Theme: {theme.name} 󰑃  {theme.description}",
                style_key="accent",
                text_style="italic",
                print_it=True,
            )
            return 0

        except Exception as e:
            logger.error(f"Error displaying current theme: {e}")
            console.print_error(f"Error displaying current theme: {e}")
            return 1

    def set_theme(self, theme_name: str) -> int:
        """Set the theme and persist it."""
        if not theme_name:
            console.print_error("Theme name cannot be empty")
            return 1

        themes = get_available_themes()
        matched = [t for t in themes if t.lower() == theme_name.lower()]

        if not matched:
            console.print_error(
                f"Theme '{theme_name}' not found. Here are the available themes:"
            )
            self.list_themes()
            return 1

        selected = matched[0]
        try:
            if set_current_theme(selected):
                if self._persist_theme(selected):
                    try:
                        display_name = get_theme(selected).display_name
                    except Exception:
                        display_name = selected

                    console.print_success(
                        f"Theme set to {display_name} and saved as default"
                    )
                else:
                    console.print_warning(
                        "Theme applied but may not persist after restart"
                    )
                return 0
            else:
                console.print_error(f"Failed to set theme to {selected}")
                return 1
        except Exception as e:
            logger.error(f"Error setting theme: {e}")
            console.print_error(f"Error setting theme: {e}")
            return 1

    def list_themes(self) -> int:
        """List available themes with the active one highlighted."""
        themes = get_available_themes()
        items = []
        name_map = {}

        for name in sorted(themes, key=str.lower):
            try:
                theme = get_theme(name)
                items.append((theme.display_name, theme.description))
                name_map[name.upper()] = theme.display_name
            except Exception:
                items.append((name, "Unknown theme"))
                name_map[name.upper()] = name

        current = get_current_theme().upper()
        current_display = name_map.get(current)
        selected_idx = next(
            (i for i, (name, _) in enumerate(items) if name == current_display), -1
        )

        from aurras.utils.console.renderer import ListDisplay

        display = ListDisplay(
            items=items,
            title="Available Themes",
            description="Use 'theme set <name>' to change the theme",
            selected_index=selected_idx,
            use_table=True,
            highlight_style="accent",
        )

        console.print(display.render())
        return 0
