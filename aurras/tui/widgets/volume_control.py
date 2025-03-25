"""
Volume control widget for Aurras TUI.
"""

from textual.containers import Horizontal
from textual.widgets import Button, Static, ProgressBar


class VolumeControl(Horizontal):
    """Widget for controlling playback volume."""

    DEFAULT_CSS = """
    VolumeControl {
        height: 3;
        align: center middle;
        padding: 0 1;
        background: $panel;
    }
    
    VolumeControl Button {
        width: 3;
        min-width: 3;
        content-align: center middle;
        background: transparent;
        border: none;
        color: $primary;
    }
    
    VolumeControl Button:hover {
        color: $accent;
        background: $selection;
    }
    
    VolumeControl .volume-bar {
        width: 20;
        height: 1;
    }
    
    VolumeControl #volume-indicator {
        width: 3;
        color: $text-muted;
        text-align: right;
    }
    """

    def __init__(self, initial_volume=70, *args, **kwargs):
        """Initialize volume control with initial volume level."""
        super().__init__(*args, **kwargs)
        self.volume = max(0, min(100, initial_volume))

    def compose(self):
        """Compose the volume control components."""
        # Use better volume icons
        yield Button("", id="volume-down", classes="volume-button")

        # Volume indicator shows percentage next to bar
        yield Static(f"{self.volume:3d}%", id="volume-indicator")

        # Visual volume bar
        yield ProgressBar(total=100, id="volume-bar", classes="volume-bar")

        yield Button("", id="volume-up", classes="volume-button")

    def on_mount(self) -> None:
        """Set initial volume level when mounted."""
        volume_bar = self.query_one("#volume-bar", ProgressBar)
        volume_bar.value = self.volume

        # Set appropriate volume icon based on level
        self._update_volume_icon()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id

        if button_id == "volume-down":
            self._decrease_volume()
        elif button_id == "volume-up":
            self._increase_volume()

    def _decrease_volume(self):
        """Decrease the volume level."""
        if self.volume > 0:
            self.volume = max(0, self.volume - 5)
            self._update_volume_display()

    def _increase_volume(self):
        """Increase the volume level."""
        if self.volume < 100:
            self.volume = min(100, self.volume + 5)
            self._update_volume_display()

    def _update_volume_display(self):
        """Update the volume display elements."""
        volume_bar = self.query_one("#volume-bar", ProgressBar)
        volume_indicator = self.query_one("#volume-indicator", Static)

        # Update the progress bar
        volume_bar.value = self.volume

        # Update the numeric indicator with proper formatting
        volume_indicator.update(f"{self.volume:3d}%")

        # Update the volume icon based on current level
        self._update_volume_icon()

        # Notify the app if it has a set_volume method
        if hasattr(self.app, "set_volume"):
            self.app.set_volume(self.volume)

    def _update_volume_icon(self):
        """Update volume icon based on current level."""
        down_button = self.query_one("#volume-down", Button)
        up_button = self.query_one("#volume-up", Button)

        # Set appropriate icons based on volume level
        if self.volume == 0:
            down_button.label = "󰝟"  # Muted icon
        elif self.volume < 33:
            down_button.label = ""  # Low volume
        elif self.volume < 66:
            down_button.label = ""  # Medium volume
        else:
            down_button.label = ""  # High volume

        # Change up button appearance based on whether we're at max
        up_button.label = "" if self.volume < 100 else "󰝞"
