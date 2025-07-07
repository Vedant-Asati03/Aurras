"""
Processors for handling various commands in the AURras application.
"""

import importlib
from aurras.utils.logger import get_logger

logger = get_logger("aurras.command.processors")


class ProcessorProvider:
    """Provider for creating processor instances with lazy loading."""

    _processor_map = {
        "self": ("aurras.utils.command.processors.self", "SelfProcessor"),
        "theme": ("aurras.utils.command.processors.theme", "ThemeProcessor"),
        "backup": ("aurras.utils.command.processors.backup", "BackupProcessor"),
        "system": ("aurras.utils.command.processors.system", "SystemProcessor"),
        "player": ("aurras.utils.command.processors.player", "PlayerProcessor"),
        "spotify": ("aurras.utils.command.processors.spotify", "SpotifyProcessor"),
        "history": ("aurras.utils.command.processors.history", "HistoryProcessor"),
        "library": ("aurras.utils.command.processors.library", "LibraryProcessor"),
        "playlist": ("aurras.utils.command.processors.playlist", "PlaylistProcessor"),
        "settings": ("aurras.utils.command.processors.settings", "SettingsProcessor"),
    }

    def __init__(self):
        self._instances = {}

    def __getattr__(self, name):
        if name.endswith("_processor"):
            processor_name = name[:-10]
            logger.debug(
                "Processor access requested", extra={"processor_name": processor_name}
            )
            return self._get_processor(processor_name)

        logger.warning(
            "Invalid attribute access attempted",
            extra={"attribute_name": name, "valid_pattern": "*_processor"},
        )
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'"
        )

    def _get_processor(self, name: str):
        """Get processor instance, creating it if needed."""
        if name not in self._instances:
            if name not in self._processor_map:
                logger.error(
                    "Unknown processor requested",
                    extra={
                        "processor_name": name,
                        "available_processors": list(self._processor_map.keys()),
                    },
                )
                raise ValueError(f"Unknown processor: {name}")

            module_path, class_name = self._processor_map[name]

            try:
                logger.debug(
                    "Creating processor instance",
                    extra={
                        "processor_name": name,
                        "module": module_path,
                        "class_name": class_name,
                    },
                )

                module = importlib.import_module(module_path)
                processor_class = getattr(module, class_name)
                self._instances[name] = processor_class()

                logger.debug(
                    "Processor instance created successfully",
                    extra={
                        "processor_name": name,
                        "total_instances": len(self._instances),
                    },
                )

            except ImportError as e:
                logger.error(
                    "Failed to import processor module",
                    extra={
                        "processor_name": name,
                        "module": module_path,
                        "error": str(e),
                    },
                )
                raise
            except AttributeError as e:
                logger.error(
                    "Failed to find processor class",
                    extra={
                        "processor_name": name,
                        "class_name": class_name,
                        "error": str(e),
                    },
                )
                raise
            except Exception as e:
                logger.error(
                    "Failed to create processor instance",
                    extra={"processor_name": name, "error": str(e), "exc_info": True},
                )
                raise

        return self._instances[name]


processor = ProcessorProvider()


__all__ = [
    "processor",
]
