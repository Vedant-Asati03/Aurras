"""
Lyrics formatter module.

This module provides functionality for formatting lyrics for display with theme integration.
"""

import random
from typing import List, Dict, Any, Tuple, Callable

from ...utils.console.manager import get_console, get_theme, get_current_theme


class LyricsFormatter:
    """Formatter for lyrics display with theme integration and highlighting."""

    def __init__(self):
        """Initialize the lyrics formatter."""
        self._console = get_console()
        # Optional simple gradient view method for subclasses to implement
        self._create_simple_gradient_view: Callable[[List[str]], str] = (
            lambda x: "\n".join(x)
        )

    def get_no_lyrics_message(self) -> str:
        """
        Get a themed "no lyrics available" message.

        Returns:
            A formatted message indicating no lyrics are available
        """
        # Get theme color with safe fallbacks
        theme_style = self._get_theme_gradient_style()
        theme_color = self._get_theme_color(theme_style)

        # List of fun messages
        unavailable_lyrics_messages = [
            f"[bold {theme_color}]No lyrics available[/bold {theme_color}]",
            f"[bold {theme_color}]Wow! so empty[/bold {theme_color}]",
            f"[bold {theme_color}]Seems like nothing came out[/bold {theme_color}]",
            f"[bold {theme_color}]Lyrics? What lyrics?[/bold {theme_color}]",
            f"[bold {theme_color}]Lyrics? I don't see any lyrics[/bold {theme_color}]",
            f"[bold {theme_color}]Lyrics? What are those?[/bold {theme_color}]",
            f"[bold {theme_color}]Lyrics? I don't think so[/bold {theme_color}]",
            f"[bold {theme_color}]Lyrics? Not today[/bold {theme_color}]",
            f"[bold {theme_color}]Uh-oh! No lyrics here[/bold {theme_color}]",
            f"[bold {theme_color}]No luck today, huh?[/bold {theme_color}]",
        ]

        return random.choice(unavailable_lyrics_messages)

    def get_waiting_message(self) -> str:
        """
        Get a themed "waiting for lyrics" message.

        Returns:
            A formatted message indicating lyrics are being fetched
        """
        theme_style = self._get_theme_gradient_style()
        theme_color = self._get_theme_color(theme_style)
        return f"[italic {theme_color}]Fetching lyrics[/italic {theme_color}]"

    def get_error_message(self, error_text: str) -> str:
        """
        Get a themed error message.

        Args:
            error_text: The error text to display

        Returns:
            A formatted error message
        """
        # Use feedback colors for consistency with user feedback
        error_text = self.apply_gradient_to_text(f"Error: {error_text}", "feedback")
        return f"[italic]{error_text}[/italic]"

    def create_focused_lyrics_view(
        self,
        lyrics_lines: List[str],
        current_time: float,
        song: str = "",
        artist: str = "",
        album: str = "",
        context_lines: int = 6,
        plain_mode: bool = False,
    ) -> str:
        """
        Create a focused view of lyrics with the current line highlighted with gradient effect.

        Args:
            lyrics_lines: List of lyrics lines
            current_time: Current playback position in seconds
            song: Song name (for logging)
            artist: Artist name (for logging)
            album: Album name
            context_lines: Number of context lines to show
            plain_mode: If True, display plain lyrics without timestamps

        Returns:
            Formatted lyrics text with gradient highlighting
        """
        from .parser import LyricsParser

        if not lyrics_lines:
            return self.get_no_lyrics_message()

        # Different display modes based on lyrics type and requested mode
        if plain_mode:
            return self._display_plain_lyrics(lyrics_lines)
        elif not LyricsParser.is_synced_lyrics(lyrics_lines):
            return self._display_plain_lyrics(lyrics_lines)
        else:
            return self._display_synced_lyrics(
                lyrics_lines, current_time, context_lines
            )

    def _display_plain_lyrics(self, lyrics_lines: List[str]) -> str:
        """Display plain lyrics with simple gradient formatting."""
        from .parser import LyricsParser

        plain_lyrics = LyricsParser.get_plain_lyrics(lyrics_lines)
        return self._create_simple_gradient_view(plain_lyrics[:15])

    def _display_synced_lyrics(
        self, lyrics_lines: List[str], current_time: float, context_lines: int
    ) -> str:
        """Display synced lyrics with the current line highlighted."""
        from .parser import LyricsParser

        # Parse timestamps and build a list of (timestamp, text) tuples
        parsed_lyrics = LyricsParser.parse_synced_lyrics(lyrics_lines)

        if not parsed_lyrics:
            return "[italic]Could not parse lyrics timestamps[/italic]"

        # Find the current line based on timestamp
        current_index = LyricsParser.find_current_lyric_index(
            parsed_lyrics, current_time
        )

        # Create gradient display
        return self._create_gradient_lyrics_view(
            parsed_lyrics, current_time, current_index, context_lines
        )

    def _create_gradient_lyrics_view(
        self,
        parsed_lyrics: List[Tuple[float, str]],
        current_time: float,
        current_index: int,
        context_lines: int,
    ) -> str:
        """
        Create a themed display for synced lyrics with word-level highlighting.

        Args:
            parsed_lyrics: List of (timestamp, text) tuples
            current_time: Current playback position in seconds
            current_index: Index of current line
            context_lines: Number of context lines to show

        Returns:
            Formatted lyrics with word-level highlighting
        """
        # Calculate the range of lines to display
        start_index = max(0, current_index - context_lines)
        end_index = min(len(parsed_lyrics), current_index + context_lines + 1)

        # Get the appropriate theme colors based on the current theme
        theme_style = self._get_theme_gradient_style()

        # Build the focused lyrics display
        result_lines = []

        # Add a header showing current position if we're not at the beginning
        if start_index > 0:
            result_lines.append(f"[{theme_style['dim']}][/{theme_style['dim']}]")

        # Add the lines with proper highlighting
        for i in range(start_index, end_index):
            timestamp, text = parsed_lyrics[i]

            if i == current_index:
                # Current line - highlight with word-level animation
                word_highlight = self._simulate_word_highlighting(
                    text, timestamp, current_time, parsed_lyrics, i, theme_style
                )
                result_lines.append(word_highlight)
            else:
                # Other lines - use theme color but dimmed
                result_lines.append(
                    f"[{theme_style['dim']}]{text}[/{theme_style['dim']}]"
                )

        # Add a footer if we're not at the end
        if end_index < len(parsed_lyrics):
            result_lines.append(f"[{theme_style['dim']}][/{theme_style['dim']}]")

        return "\n".join(result_lines)

    def _simulate_word_highlighting(
        self,
        text: str,
        line_start_time: float,
        current_time: float,
        parsed_lyrics: List[Tuple[float, str]],
        line_index: int,
        theme_style: Dict[str, Any],
    ) -> str:
        """
        Simulate word-level highlighting for standard LRC format.

        Args:
            text: The line text
            line_start_time: Timestamp of current line
            current_time: Current playback position
            parsed_lyrics: All parsed lyrics
            line_index: Current line index
            theme_style: Theme style dictionary

        Returns:
            Formatted text with simulated word-level highlighting
        """
        # Split the line into words
        words = text.split()
        if not words:
            return text

        # Calculate the end time of this line (start of next line or estimate)
        line_end_time = None
        if line_index < len(parsed_lyrics) - 1:
            line_end_time = parsed_lyrics[line_index + 1][0]
        else:
            # For the last line, estimate duration based on average line duration
            if line_index > 0:
                prev_duration = line_start_time - parsed_lyrics[line_index - 1][0]
                line_end_time = line_start_time + prev_duration
            else:
                # Default to 5 seconds if we can't estimate
                line_end_time = line_start_time + 5

        # Calculate line duration
        line_duration = line_end_time - line_start_time

        # Time elapsed since start of the line
        elapsed_in_line = current_time - line_start_time

        # If elapsed time is negative, we're still before this line starts
        if elapsed_in_line < 0:
            return f"[{theme_style['dim']}]{text}[/{theme_style['dim']}]"

        # Calculate which word should be highlighted based on elapsed time percentage
        total_chars = (
            sum(len(word) for word in words) + len(words) - 1
        )  # Include spaces

        # Calculate "progress" through the line (0.0 to 1.0)
        progress = min(1.0, elapsed_in_line / line_duration)

        # Calculate which character we're at based on progress
        target_char_pos = int(progress * total_chars)

        # Figure out which word this corresponds to
        current_word_index = 0
        char_count = 0

        for i, word in enumerate(words):
            char_count += len(word)
            if i < len(words) - 1:
                char_count += 1  # Account for space
            if char_count > target_char_pos:
                current_word_index = i
                break

        # Use our existing word highlighting function with the theme style
        return self._highlight_current_word(
            [{"text": word} for word in words], current_word_index, theme_style
        )

    def _highlight_current_word(
        self,
        words: List[Dict[str, Any]],
        current_word_index: int,
        theme_style: Dict[str, Any],
    ) -> str:
        """
        Create a string with the current word highlighted using a gradient effect.

        Args:
            words: List of word data dictionaries
            current_word_index: Index of the current word
            theme_style: Theme style dictionary

        Returns:
            Formatted string with prominent gradient word highlighting
        """
        # Get theme colors with fallbacks
        theme_color = self._get_theme_color(theme_style)
        gradient_colors = theme_style.get("title", ["#00FF7F", "#00DD6E", "#00BB5C"])
        dim_color = theme_style.get("dim", "#555555")

        # Format each word based on its distance from the current word
        formatted_words = []
        for i, word_data in enumerate(words):
            word_text = word_data["text"]
            distance = abs(i - current_word_index)

            formatted_words.append(
                self._format_word_with_gradient(
                    word_text, distance, theme_color, gradient_colors, dim_color
                )
            )

        return " ".join(formatted_words)

    def _format_word_with_gradient(
        self,
        word: str,
        distance: int,
        theme_color: str,
        gradient_colors: List[str],
        dim_color: str,
    ) -> str:
        """Format a single word based on its distance from the current word."""
        # Current or adjacent word - use primary color and bold
        if distance <= 1:
            return f"[bold {theme_color}]{word}[/bold {theme_color}]"

        # Words within gradient range - use gradient colors
        if distance <= len(gradient_colors) + 1:
            # Index into gradient colors, with bounds checking
            color_index = min(distance - 2, len(gradient_colors) - 1)
            color_index = max(0, color_index)  # Ensure non-negative
            color = gradient_colors[color_index]
            return f"[{color}]{word}[/{color}]"

        # Far words - use dim color
        return f"[{dim_color}]{word}[/{dim_color}]"

    def _get_theme_gradient_style(self) -> Dict[str, Any]:
        """Get the gradient style based on the current theme."""
        # Get theme from unified theme system
        current_theme = get_current_theme()
        theme = get_theme(current_theme)

        # Use adapters to get theme styles instead of direct method call
        from ...themes.adapters import get_gradient_styles

        theme_gradients = get_gradient_styles(theme)
        return theme_gradients

    def _get_theme_color(self, theme_style: Dict[str, Any]) -> str:
        """Get the primary theme color with appropriate fallbacks."""
        return theme_style.get("primary", theme_style.get("title", ["#00FF7F"])[0])

    def apply_gradient_to_text(
        self, text: str, gradient_key: str, bold: bool = False
    ) -> str:
        """
        Apply a gradient effect to text based on the current theme.

        Args:
            text: The text to apply gradient to
            gradient_key: Which gradient to use ('title', 'artist', etc.)
            bold: Whether to make the text bold

        Returns:
            str: Rich-formatted text with gradient applied
        """
        style = self._get_theme_gradient_style()
        gradient = style.get(gradient_key, style["title"])  # Default to title gradient

        if not text or len(gradient) == 0:
            return text

        # For very short text, just use the first color
        if len(text) <= 3:
            bold_prefix = "bold " if bold else ""
            return f"[{bold_prefix}{gradient[0]}]{text}[/{bold_prefix}{gradient[0]}]"

        # For longer text, create a gradient effect
        chars_per_color = max(1, len(text) // len(gradient))
        result = []

        for i, char in enumerate(text):
            color_index = min(i // chars_per_color, len(gradient) - 1)
            color = gradient[color_index]
            bold_prefix = "bold " if bold else ""
            result.append(f"[{bold_prefix}{color}]{char}[/{bold_prefix}{color}]")

        return "".join(result)
