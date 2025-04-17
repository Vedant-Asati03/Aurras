"""
Completer Registry Module

This module provides a registry for prompt_toolkit completers based on input patterns.
"""

import re
from prompt_toolkit.completion import Completer
from typing import Dict, List, Tuple, Pattern, Optional, Union


class CompleterRegistry:
    """Registry for prompt_toolkit completers based on input patterns."""

    def __init__(self):
        """Initialize the CompleterRegistry."""
        self.prefix_completers: Dict[str, Completer] = {}
        self.pattern_completers: List[Tuple[Pattern, Completer]] = []
        self.default_completer: Optional[Completer] = None

    def register_prefix(self, prefix: str, completer: Completer) -> None:
        """
        Register a completer for a specific prefix.

        Args:
            prefix: The prefix to match (e.g., "?", ">")
            completer: The completer to use for this prefix
        """
        self.prefix_completers[prefix] = completer

    def register_pattern(
        self, pattern: Union[str, Pattern], completer: Completer
    ) -> None:
        """
        Register a completer for a regex pattern.

        Args:
            pattern: The regex pattern to match
            completer: The completer to use for this pattern
        """
        if isinstance(pattern, str):
            pattern = re.compile(pattern)
        self.pattern_completers.append((pattern, completer))

    def set_default_completer(self, completer: Completer) -> None:
        """
        Set the default completer to use when no patterns match.

        Args:
            completer: The default completer
        """
        self.default_completer = completer

    def get_completer_for_input(self, text: str) -> Completer:
        """
        Get the appropriate completer for the given input text.

        Args:
            text: The input text to match against

        Returns:
            The matching completer, or the default completer if no match
        """
        # Check prefix completers first (faster than regex)
        for prefix, completer in self.prefix_completers.items():
            if text.startswith(prefix):
                return completer

        # Check pattern completers
        for pattern, completer in self.pattern_completers:
            if pattern.match(text):
                return completer

        # Fall back to default completer
        return self.default_completer
