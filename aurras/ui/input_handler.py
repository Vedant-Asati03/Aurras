from prompt_toolkit import prompt
from prompt_toolkit.styles import Style
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from rich.console import Console
from rich.panel import Panel

from ..ui.command_handler import InputCases
from ..ui.search_bar import DynamicSearchBar
from ..ui.suggestions.history import SuggestSongsFromHistory
from ..ui.shortcut_handler import HandleShortcutInputs
from ..player.online import ListenSongOnline
from ..player.queue import QueueManager
from ..ui.command_palette import CommandPalette


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

            # Parse the command palette selection
            if ":" in command_text:
                command_name = command_text.split(":", 1)[0].strip()
                self._execute_command_palette_action(command_name)
                return

            # Handle Cancel command
            if command_text == "Cancel" or command_text == "cancel":
                console.print("[dim]Command cancelled.[/dim]")
                return

            # If command doesn't match format, try direct command execution
            palette = CommandPalette()
            for cmd_id, cmd in palette.commands.items():
                if cmd["name"].lower() == command_text.lower():
                    console.print(f"[bold cyan]Executing:[/bold cyan] {cmd['name']}")
                    cmd["action"]()
                    return

        # Check for other command palette activations
        elif self.user_input == "cmd" or self.user_input == "command_palette":
            console.print("[bold cyan]Opening command palette...[/bold cyan]")
            CommandPalette().show_command_palette()
            return

        # Check for command matches with display names from command palette
        palette = CommandPalette()
        for cmd_id, cmd in palette.commands.items():
            if (
                f"{cmd['name'].lower()}: {cmd['description'].lower()}"
                == self.user_input.lower()
            ):
                console.print(f"[bold cyan]Executing:[/bold cyan] {cmd['name']}")
                cmd["action"]()
                return
            elif cmd["name"].lower() == self.user_input.lower():
                console.print(f"[bold cyan]Executing:[/bold cyan] {cmd['name']}")
                cmd["action"]()
                return

        if "," in self.user_input:
            songs = [s.strip() for s in self.user_input.split(",") if s.strip()]
            if songs:
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
                "cache_info": self.case.show_cache_info,
                "cleanup_cache": self.case.cleanup_cache,
                "view_playlist": self.case.view_playlist,
                "add_song_to_playlist": self.case.add_song_to_playlist,
                "remove_song_from_playlist": self.case.remove_song_from_playlist,
                "move_song_up": lambda: self.case.move_song_in_playlist("up"),
                "move_song_down": lambda: self.case.move_song_in_playlist("down"),
                "shuffle_playlist": self.case.shuffle_playlist,
                "setup_spotify": self.case.setup_spotify,
            }

            if self.user_input.startswith("cleanup_cache "):
                parts = self.user_input.split(" ", 1)
                if len(parts) == 2 and parts[1].isdigit():
                    console.print(
                        f"[bold cyan]Cleaning cache older than {parts[1]} days[/bold cyan]"
                    )
                    self.case.cleanup_cache(int(parts[1]))
                    return

            if self.user_input.startswith("pl "):
                playlist_name = self.user_input[3:].strip()
                if playlist_name:
                    console.print(
                        f"[bold cyan]Viewing playlist:[/bold cyan] {playlist_name}"
                    )
                    self.case.view_playlist(playlist_name)
                    return

            # Fix: Add support for "plp" shortcut for play_playlist
            if self.user_input.startswith("plp "):
                playlist_name = self.user_input[4:].strip()
                if playlist_name:
                    console.print(
                        f"[bold cyan]Playing playlist:[/bold cyan] {playlist_name}"
                    )
                    self.case.play_playlist("n", playlist_name)
                    return

            if self.user_input.startswith("spl "):
                playlist_name = self.user_input[4:].strip()
                if playlist_name:
                    console.print(
                        f"[bold cyan]Playing shuffled playlist:[/bold cyan] {playlist_name}"
                    )
                    self.case.shuffle_playlist("n", playlist_name)
                    return

            if self.user_input.startswith("aps "):
                # Format: "aps playlist_name, song_name"
                try:
                    params = self.user_input[4:].split(",", 1)
                    if len(params) == 2:
                        playlist_name = params[0].strip()
                        song_name = params[1].strip()
                        console.print(
                            f"[bold cyan]Adding song to playlist:[/bold cyan] {song_name} → {playlist_name}"
                        )
                        self.case.add_song_to_playlist(playlist_name, song_name)
                        return
                except:
                    pass

            if self.user_input.startswith("rps "):
                # Format: "rps playlist_name, song_name"
                try:
                    params = self.user_input[4:].split(",", 1)
                    if len(params) == 2:
                        playlist_name = params[0].strip()
                        song_name = params[1].strip()
                        console.print(
                            f"[bold cyan]Removing song from playlist:[/bold cyan] {song_name} from {playlist_name}"
                        )
                        self.case.remove_song_from_playlist(playlist_name, song_name)
                        return
                except:
                    pass

            if self.user_input in actions:
                console.print(f"[bold cyan]Executing:[/bold cyan] {self.user_input}")
                actions[self.user_input]()
                return

            else:
                console.rule(f"[bold green]Playing: {self.user_input}")
                self.case.song_searched(self.user_input)
                return

    def _execute_command_palette_action(self, command_name):
        """Execute a command from the command palette by name."""
        palette = CommandPalette()

        for cmd_id, cmd in palette.commands.items():
            if cmd["name"].lower() == command_name.lower():
                console.print(f"[bold cyan]Executing:[/bold cyan] {cmd['name']}")
                cmd["action"]()
                return

        # If command not found, show an error
        console.print(f"[bold red]Unknown command:[/bold red] {command_name}")
