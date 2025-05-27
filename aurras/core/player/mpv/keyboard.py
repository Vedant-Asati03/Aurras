"""
Keyboard control handling for the MPV player.

This module contains keyboard bindings and handlers for the MPV player interface.
"""

from aurras.core.settings import SETTINGS
from aurras.utils.logger import get_logger
from aurras.core.player.mpv.state import FeedbackType, PlaybackState, LyricsStatus

logger = get_logger("aurras.core.player.keyboard", log_to_console=False)


def setup_key_bindings(player) -> None:
    """
    Set up keyboard controls for the player.

    Args:
        player: The MPVPlayer instance
    """

    # Quit handler
    @player.on_key_press(SETTINGS.keyboard_shortcuts.quit_playback)
    def _quit() -> None:
        # Let user know we're quitting
        player._show_user_feedback("Quit", "Exiting player", FeedbackType.SYSTEM)

        try:
            # Mark the player as stopping FIRST to prevent new operations
            player._state.stop_requested = True
            player._state.playback_state = PlaybackState.STOPPED

            # Unregister all observers to prevent callback race conditions
            if hasattr(player, "_observers"):
                for observer in player._observers:
                    try:
                        observer.unregister()
                    except Exception as e:
                        logger.debug(f"Error unregistering observer: {e}")
                player._observers = []

            # Cancel any pending operations
            if (
                hasattr(player, "_lyrics")
                and player._lyrics.future
                and not player._lyrics.future.done()
            ):
                player._lyrics.future.cancel()

            player.terminate()
        except Exception as e:
            logger.error(f"Error during player shutdown: {e}")

    # Volume control
    @player.on_key_press(SETTINGS.keyboard_shortcuts.volume_up)
    def _volume_up() -> None:
        new_volume = min(float(SETTINGS.maximum_volume), player.volume + 5)
        player.volume = new_volume
        player._show_user_feedback(
            "Volume", f"Increased to {new_volume}%", FeedbackType.VOLUME
        )

    @player.on_key_press(SETTINGS.keyboard_shortcuts.volume_down)
    def _volume_down() -> None:
        new_volume = max(0, player.volume - 5)
        player.volume = new_volume
        player._show_user_feedback(
            "Volume", f"Decreased to {new_volume}%", FeedbackType.VOLUME
        )

    # Toggle lyrics display
    @player.on_key_press(SETTINGS.keyboard_shortcuts.toggle_lyrics)
    def _toggle_lyrics() -> None:
        player._state.show_lyrics = not player._state.show_lyrics
        action = "Showing" if player._state.show_lyrics else "Hiding"

        if not player._state.show_lyrics:
            player._lyrics.status = LyricsStatus.DISABLED
        elif player._lyrics.cached_lyrics:
            player._lyrics.status = LyricsStatus.AVAILABLE
        else:
            player._lyrics.status = LyricsStatus.LOADING

        player._show_user_feedback(
            "Lyrics", f"{action} lyrics display", FeedbackType.LYRICS
        )

    # Seeking
    @player.on_key_press(SETTINGS.keyboard_shortcuts.seek_forward)
    def _seek_forward() -> None:
        player.seek(10)
        player._show_user_feedback("Seek", "Forward 10s", FeedbackType.SEEKING)

    @player.on_key_press(SETTINGS.keyboard_shortcuts.seek_backward)
    def _seek_backward() -> None:
        player.seek(-10)
        player._show_user_feedback("Seek", "Backward 10s", FeedbackType.SEEKING)

    # Reset jump mode state
    player._state.jump_mode = False
    player._state.jump_number = ""

    # Number key Handler
    def _handle_number_key(key: str) -> None:
        player._state.jump_mode = True
        player._state.jump_number += key
        player._show_user_feedback(
            "Jump Mode",
            f"Jump {player._state.jump_number} tracks, press {SETTINGS.keyboard_shortcuts.previous_track}/{SETTINGS.keyboard_shortcuts.next_track}",
            FeedbackType.NAVIGATION,
        )

    # Register the number key handlers with proper argument handling
    for digit in "0123456789":
        # Accept all 5 args passed by mpv but only use the digit we care about
        player.register_key_binding(
            digit,
            lambda _state, _name, _char, _scale, _arg, digit=digit: _handle_number_key(
                digit
            ),
        )

    # Next and previous handlers (Supports jump mode)
    @player.on_key_press(SETTINGS.keyboard_shortcuts.next_track)
    def _next_track() -> None:
        if player._state.jump_mode:
            try:
                jump_amount = (
                    int(player._state.jump_number) if player._state.jump_number else 1
                )
                player._execute_playlist_jump(jump_amount)
                player._show_user_feedback(
                    "Jump", f"Forward {jump_amount} tracks", FeedbackType.NAVIGATION
                )
            except ValueError:
                player._show_user_feedback(
                    "Error", "Invalid jump number", FeedbackType.ERROR
                )
            finally:
                player._state.jump_mode = False
                player._state.jump_number = ""
        else:
            player._show_user_feedback(
                "Next", "Playing next track", FeedbackType.NAVIGATION
            )
            player.playlist_next()

    @player.on_key_press(SETTINGS.keyboard_shortcuts.previous_track)
    def _prev_track() -> None:
        if player._state.jump_mode:
            try:
                jump_amount = (
                    int(player._state.jump_number) if player._state.jump_number else 1
                )
                player._execute_playlist_jump(-jump_amount)
                player._show_user_feedback(
                    "Jump", f"Backward {jump_amount} tracks", FeedbackType.NAVIGATION
                )
            except ValueError:
                player._show_user_feedback(
                    "Error", "Invalid jump number", FeedbackType.ERROR
                )
            finally:
                player._state.jump_mode = False
                player._state.jump_number = ""
        else:
            player._show_user_feedback(
                "Previous", "Playing previous track", FeedbackType.NAVIGATION
            )
            player.playlist_prev()

    # Escape key to cancel jump mode
    @player.on_key_press(SETTINGS.keyboard_shortcuts.stop_jump_mode)
    def _cancel_jump_mode() -> None:
        if player._state.jump_mode:
            player._state.jump_mode = False
            player._state.jump_number = ""
            player._show_user_feedback(
                "Jump Mode", "Cancelled", FeedbackType.NAVIGATION
            )

    # Cycle themes
    @player.on_key_press(SETTINGS.keyboard_shortcuts.switch_themes)
    def _cycle_theme() -> None:
        from aurras.utils.console.manager import (
            change_theme,
            get_available_themes,
            get_current_theme,
        )

        available_themes = get_available_themes()
        current_theme = get_current_theme()

        try:
            current_index = available_themes.index(current_theme)
            # Get the next theme (wrapping around)
            next_index = (current_index + 1) % len(available_themes)
            next_theme = available_themes[next_index]

            change_theme(next_theme)
            player._state.current_theme = next_theme

            # Force cache reset for any theme-dependent elements
            player._lyrics.cached_lyrics = None

            player._show_user_feedback(
                "Theme", f"Changed to {next_theme}", FeedbackType.THEME
            )
        except ValueError:
            next_theme = available_themes[0]
            change_theme(next_theme)
            player._state.current_theme = next_theme

            player._lyrics.cached_lyrics = None

            player._show_user_feedback(
                "Theme", f"Changed to {next_theme}", FeedbackType.THEME
            )
