"""
UI Renderers for Aurras Music Player.

This package contains components that render UI elements to the user:
- command_palette: Command palette renderer
- options_palette: Options palette renderer
"""

from aurras.utils.logger import get_logger
from aurras.ui.renderers.command_palette import CommandPalette
from aurras.ui.renderers.options_palette import options

logger = get_logger("aurras.ui.renderers", log_to_console=False)

command_palette = CommandPalette()
logger.debug("Command palette initialized.")


__all__ = ["command_palette", "options"]
