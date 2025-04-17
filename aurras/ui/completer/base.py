"""
Base Completer Module

This module provides a base class for all Aurras completers.
"""

from typing import List, Tuple
from abc import ABC, abstractmethod
from prompt_toolkit.completion import Completer, Completion


class BaseCompleter(Completer, ABC):
    """Base class for all Aurras completers."""

    @abstractmethod
    def get_suggestions(self, text: str) -> List[Tuple[str, str]]:
        """
        Get suggestion items for the given text.

        Args:
            text: The input text to get suggestions for

        Returns:
            List of tuples (completion_text, description)
        """
        pass

    def get_completions(self, document, complete_event):
        """
        Standard implementation that uses get_suggestions.

        This method converts suggestion tuples to Completion objects.
        """
        text = document.text_before_cursor

        suggestions = self.get_suggestions(text)

        for completion_text, description in suggestions:
            yield Completion(
                completion_text,
                start_position=-len(text),
                display=completion_text,
                display_meta=description,
            )
