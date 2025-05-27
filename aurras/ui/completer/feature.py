from typing import List, Tuple

from aurras.ui.renderers import options
from aurras.core.settings import SETTINGS
from aurras.ui.completer.base import BaseCompleter


class FeatureCompleter(BaseCompleter):
    """
    Auto-completion class for AurrasApp features.

    Provides suggestions for app features when the '?' prefix is used.
    """

    def __init__(self):
        """
        Initializes the SuggestAppFeatures class.
        """

    def get_suggestions(self, text: str) -> List[Tuple[str, str]]:
        """
        Get app feature suggestions.

        Args:
            text: The input text with prefix

        Returns:
            List of tuples (feature_name, "Feature")
        """
        if text.startswith(SETTINGS.options_menu_key):
            return [(name, desc) for name, desc in options.items()]
        return []
