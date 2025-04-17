from typing import List, Tuple
from .base import BaseCompleter


class FeatureCompleter(BaseCompleter):
    """
    Auto-completion class for AurrasApp features.

    Provides suggestions for app features when the '?' prefix is used.
    """

    def __init__(self):
        """
        Initializes the SuggestAppFeatures class.
        """
        self.app_features = [
            "Help",
            "Play_Offline",
            "Download_Song",
            "Play_Playlist",
            "Delete_Playlist",
            "Import_Playlist",
            "Download_Playlist",
            "Settings",
            "Command_Palette",
            ">",
            "cmd",
        ]

    def get_suggestions(self, text: str) -> List[Tuple[str, str]]:
        """
        Get app feature suggestions.

        Args:
            text: The input text with prefix

        Returns:
            List of tuples (feature_name, "Feature")
        """
        if text.startswith("?"):
            return [(command, "Feature") for command in self.app_features]
        return []
