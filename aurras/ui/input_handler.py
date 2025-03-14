from prompt_toolkit import prompt
from prompt_toolkit.styles import Style
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
import time
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from ..utils.terminal import clear_screen
from ..ui.command_handler import InputCases
from ..ui.search_bar import DynamicSearchBar
from ..ui.suggestions.history import SuggestSongsFromHistory
from ..ui.command_palette import DisplaySettings
from ..ui.shortcut_handler import HandleShortcutInputs
from ..player.online import ListenSongOnline
from ..player.queue import QueueManager
from ..ui.command_palette import CommandPalette

# Create a console for rich output
console = Console()


class HandleUserInput:
    def __init__(self):
        """
        Initialize the AurrasApp class.
        """
        self.user_input = None
        self.case = InputCases()
        self.dynamic_search_bar = DynamicSearchBar()
        self.queue_manager = QueueManager()

    def _set_placeholder_style(self):
        style = Style.from_dict(
            {
                "placeholder": "#AAAAAA italic",
                "prompt": "bold cyan",
            }
        )
        return style

    def _get_user_input(self):
        """
        Get user input for song search.
        """
        self.user_input = (
            prompt(
                message="\n🎵 › ",
                completer=self.dynamic_search_bar,
                placeholder="Search for a song or type a command... (Press > for command palette)",
                style=self._set_placeholder_style(),
                complete_while_typing=True,
                clipboard=True,
                mouse_support=True,
                history=SuggestSongsFromHistory(),
                auto_suggest=AutoSuggestFromHistory(),
                complete_in_thread=True,
            )
            .strip("?")
            .strip()
            .lower()
        )

        # Don't print empty input processing message
        if self.user_input:
            console.print(f"[dim]Processing: '{self.user_input}'[/dim]")

    def handle_user_input(self):
        """
        Handle user input based on the selected song.
        """
        self._get_user_input()

        # If input is empty, get new input
        if not self.user_input:
            return

        # Check for command palette activation via > command
        if self.user_input.startswith(">"):
            # Extract the command name from the input
            command_text = self.user_input[1:].strip()

            # If it's just ">" without a command, open the full palette
            if not command_text or command_text == "":
                console.print("[bold cyan]Opening command palette...[/bold cyan]")
                CommandPalette().show_command_palette()
                return

            # Otherwise, try to execute the selected command directly
            palette = CommandPalette()

            if command_text == "Cancel":
                return

            # Try to find and execute the command
            for cmd_id, cmd in palette.commands.items():
                cmd_name = cmd["name"]
                cmd_desc = cmd["description"]
                display = f"{cmd_name}: {cmd_desc}"

                if command_text == display or command_text.startswith(f"{cmd_name}:"):
                    console.print(f"[bold cyan]Executing:[/bold cyan] {cmd_name}")
                    cmd["action"]()
                    return

        # Check for other command palette activations
        elif self.user_input == "cmd" or self.user_input == "command_palette":
            console.print("[bold cyan]Opening command palette...[/bold cyan]")
            CommandPalette().show_command_palette()
            return

        # First check for comma-separated songs - this should take highest priority
        if "," in self.user_input:
            songs = [s.strip() for s in self.user_input.split(",") if s.strip()]
            if songs:
                # Create a nice panel to show the playlist
                console.print(
                    Panel(
                        "\n".join(
                            [
                                f"[cyan]{i}.[/cyan] {song}"
                                for i, song in enumerate(songs, 1)
                            ]
                        ),
                        title="Song Playlist",
                        border_style="green",
                    )
                )

                try:
                    # Play each song directly in sequence
                    for i, song in enumerate(songs):
                        console.rule(
                            f"[bold green]Now playing: {song} [{i + 1}/{len(songs)}]"
                        )
                        player = ListenSongOnline(song)
                        player.listen_song_online()
                except KeyboardInterrupt:
                    console.print("\n[yellow]Playback interrupted[/yellow]")
                except Exception as e:
                    console.print(
                        f"\n[bold red]Error during playback:[/bold red] {str(e)}"
                    )

                return

        # Check for special keyboard shortcuts
        elif self.user_input == "b" or self.user_input == "back":
            console.print("[cyan]Finding previous song...[/cyan]")
            self.case.play_previous()
            return

        # Only check shortcuts if not comma-separated
        check_if_shortcut_used = HandleShortcutInputs(
            self.user_input
        ).handle_shortcut_input()

        if check_if_shortcut_used == "shortcut_not_used":
            actions = {
                "help": self.case.display_help,
                "play_offline": self.case.play_offline,
                "download_song": self.case.download_song,
                "play_playlist": self.case.play_playlist,
                "delete_playlist": self.case.delete_playlist,
                "import_playlist": self.case.import_playlist,
                "download_playlist": self.case.download_playlist,
                "queue": self.case.show_queue,
                "clear_queue": self.case.clear_queue,
                "history": self.case.show_history,
                "previous": self.case.play_previous,
                "clear_history": self.case.clear_history,
                "toggle_lyrics": self.case.toggle_lyrics,
                "cache_info": self.case.show_cache_info,  # Add new command
                "cleanup_cache": self.case.cleanup_cache,  # Add new command
            }

            # Check if it's the cleanup_cache command with arguments
            if self.user_input.startswith("cleanup_cache "):
                parts = self.user_input.split(" ", 1)
                if len(parts) == 2 and parts[1].isdigit():
                    console.print(
                        f"[bold cyan]Cleaning cache older than {parts[1]} days[/bold cyan]"
                    )
                    self.case.cleanup_cache(int(parts[1]))
                    return

            # Check for commands
            if self.user_input in actions:
                console.print(f"[bold cyan]Executing:[/bold cyan] {self.user_input}")
                actions[self.user_input]()
                return

            # Default to single song
            else:
                console.rule(f"[bold green]Playing: {self.user_input}")
                self.case.song_searched(self.user_input)
                return
