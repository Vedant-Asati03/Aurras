"""
Lyrics formatter module.

This module provides functionality for formatting lyrics for display with theme integration.
"""

import random
from typing import List, Dict, Any, Tuple, Callable

from aurras.utils.console import console
from aurras.services.lyrics.parser import LyricsParser


class LyricsFormatter:
    """Formatter for lyrics display with theme integration and highlighting."""

    def __init__(self):
        """Initialize the lyrics formatter."""
        self._create_simple_gradient_view: Callable[[List[str]], str] = (
            lambda x: "\n".join(x)
        )
        self.parser = LyricsParser()

    def get_no_lyrics_message(self) -> str:
        """
        Get a themed "no lyrics available" message.

        Returns:
            A formatted message indicating no lyrics are available
        """
        unavailable_lyrics_messages = [
            "No lyrics available[/]",
            "Wow! so empty[/]",
            "Seems like nothing came out[/]",
            "Lyrics? What lyrics?[/]",
            "Lyrics? I don't see any lyrics[/]",
            "Lyrics? What are those?[/]",
            "Lyrics? I don't think so[/]",
            "Lyrics? Not today[/]",
            "Uh-oh! No lyrics here[/]",
            "No luck today, huh?[/]",
        ]
        stlyed_messages = [
            f"[bold {console.text_muted}]{message}"
            for message in unavailable_lyrics_messages
        ]

        return random.choice(stlyed_messages)

    def get_waiting_message(self) -> str:
        """
        Get a themed "waiting for lyrics" message.

        Returns:
            A formatted message indicating lyrics are being fetched
        """
        return f"[italic {console.info}]Fetching lyrics[/]"

    def get_error_message(self, error_text: str) -> str:
        """
        Get a themed error message.

        Args:
            error_text: The error text to display

        Returns:
            A formatted error message
        """
        error_text = self.apply_gradient_to_text(f"Error: {error_text}", "feedback")
        return f"[italic]{error_text}[/italic]"

    def create_focused_lyrics_view(
        self,
        lyrics_lines: List[str],
        current_time: float,
        duration: float,
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
        if not lyrics_lines:
            return self.get_no_lyrics_message()

        if not self.parser.is_synced_lyrics(lyrics_lines) or plain_mode:
            return self._display_plain_lyrics(lyrics_lines, current_time, duration)

        return self._display_synced_lyrics(lyrics_lines, current_time, context_lines)

    def _display_plain_lyrics(
        self, lyrics_lines: List[str], current_time: float, duration: float
    ) -> str:
        """
        Display plain lyrics with simple gradient formatting based on current playback time.

        Args:
            lyrics_lines: List of lyrics lines
            current_time: Current playback position in seconds

        Returns:
            Formatted lyrics text with the appropriate chunk visible
        """
        plain_lyrics = self.parser.get_plain_lyrics(lyrics_lines)

        if not plain_lyrics:
            return self.get_no_lyrics_message()

        CHUNK_SIZE = 15  # Number of lines to show at once

        # Calculate which chunk of lyrics to show
        total_chunks = max(1, len(plain_lyrics) // CHUNK_SIZE)
        current_chunk = min(
            int((current_time / duration) * total_chunks), total_chunks - 1
        )

        # Calculate the start and end indices
        start_index = current_chunk * CHUNK_SIZE
        end_index = min(start_index + CHUNK_SIZE, len(plain_lyrics))

        # Get the current lyrics chunk
        current_chunk_lyrics = plain_lyrics[start_index:end_index]

        result_lines = []

        for line in current_chunk_lyrics:
            styled_line = console.style_text(text=line, style_key="primary")
            result_lines.append(styled_line)

        return self._create_simple_gradient_view(result_lines)

    def _display_synced_lyrics(
        self, lyrics_lines: List[str], current_time: float, context_lines: int
    ) -> str:
        """Display synced lyrics with the current line highlighted."""
        # Parse timestamps and build a list of (timestamp, text) tuples
        parsed_lyrics = self.parser.parse_synced_lyrics(lyrics_lines)

        if not parsed_lyrics:
            return "[italic]Could not parse lyrics timestamps[/italic]"

        # Find the current line based on timestamp
        current_index = self.parser.find_current_lyric_index(
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

        # Build the focused lyrics display
        result_lines = []

        # Add a header showing current position if we're not at the beginning
        if start_index > 0:
            result_lines.append(f"[{console.dim}][/{console.dim}]")

        # Add the lines with proper highlighting
        for i in range(start_index, end_index):
            timestamp, text = parsed_lyrics[i]

            if i == current_index:
                # Current line - highlight with word-level animation
                word_highlight = self._simulate_word_highlighting(
                    text, timestamp, current_time, parsed_lyrics, i
                )
                result_lines.append(word_highlight)
            else:
                # Other lines - use theme color but dimmed
                result_lines.append(console.style_text(text=text, style_key="text_muted"))

        # Add a footer if we're not at the end
        if end_index < len(parsed_lyrics):
            result_lines.append(console.style_text(text="", style_key="text_muted"))

        return "\n".join(result_lines)

    def _simulate_word_highlighting(
        self,
        text: str,
        line_start_time: float,
        current_time: float,
        parsed_lyrics: List[Tuple[float, str]],
        line_index: int,
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
            stlyed_text = console.style_text(text=text, style_key="text_muted")
            return stlyed_text

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
            [{"text": word} for word in words], current_word_index
        )

    def _highlight_current_word(
        self,
        words: List[Dict[str, Any]],
        current_word_index: int,
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
        # Format each word based on its distance from the current word
        formatted_words = []
        for i, word_data in enumerate(words):
            word_text = word_data["text"]
            distance = abs(i - current_word_index)

            formatted_words.append(self._format_word_with_gradient(word_text, distance))

        return " ".join(formatted_words)

    def _format_word_with_gradient(
        self,
        word: str,
        distance: int,
    ) -> str:
        """Format a single word based on its distance from the current word."""
        # Current or adjacent word - use primary color and bold
        if distance <= 1:
            styled_word = console.style_text(text=word, style_key="primary")
            return styled_word

        # Words within gradient range - use gradient colors
        if distance <= len(console.title_gradient) + 1:
            # Index into gradient colors, with bounds checking
            color_index = min(distance - 2, len(console.title_gradient) - 1)
            color_index = max(0, color_index)  # Ensure non-negative
            color = console.title_gradient[color_index]
            return f"[{color}]{word}[/{color}]"

        # Far words - use dim color
        return console.style_text(text=word, style_key="text_muted")
