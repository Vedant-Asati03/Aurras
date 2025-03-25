from textual.widgets import Static


class Empty(Static):
    """Widget showing an empty state with a message."""

    def __init__(self, message: str = "Wow! So empty here.", border_title = None):
        """Initialize the empty widget with an optional message.

        Args:
            message: The message to display. Defaults to "Wow! So empty here."
        """
        super().__init__(message, classes="empty")
        self.border_title = border_title
