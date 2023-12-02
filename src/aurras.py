"""
...
"""

import sys
from pathlib import Path
from rich.console import Console

# Add the project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils.decorators import handle_exceptions
from src.scripts.input_handler import HandleUserInput


class AurrasApp:
    """
    AurrasApp class for handling the Aurras music player application.

    Attributes:
    - console (Console): Rich Console for printing messages.
    - recent_songs (RecentSongs): Instance of the RecentSongs class for handling command history.
    """

    def __init__(self) -> None:
        self.handle_input = HandleUserInput()
        self.console = Console()

    @handle_exceptions
    def run(self):
        """Run the AurrasApp"""
        while True:
            self.handle_input.handle_user_input()


if __name__ == "__main__":
    aurras_app = AurrasApp()

    # Apply the handle_exceptions decorator to the run method
    run_with_exceptions = handle_exceptions(aurras_app.run)

    try:
        run_with_exceptions()

    except KeyboardInterrupt:
        aurras_app.console.print("[bold green]Thanks for using aurras![/]")

    except Exception:
        aurras_app.console.print("[bold red]Oh no! An unknown error occurred.[/]")
        aurras_app.console.print(
            "[bold red]Please report it on https://github.com/Vedant-Asati03/aurras/issues with the following exception traceback:[/]"
        )
        aurras_app.console.print_exception()

    # except Exception as e:
    #     # Catch the specific exception raised by the handle_exceptions decorator
    #     if isinstance(
    #         e, (PlaylistNotFoundError, SongsNotFoundError, NotAuthenticatedError)
    #     ):
    #         aurras_app.console.print(f"[bold red]Error: {e}[/]")
    #         # Handle specific exceptions here
    #     else:
    #         # Handle other unexpected exceptions
    #         aurras_app.console.print("[bold red]Oh no! An unknown error occurred.[/]")
    #         aurras_app.console.print(
    #             "[bold red]Please report it on https://github.com/Vedant-Asati03/aurras/issues with the following exception traceback:[/]"
    #         )
    #         aurras_app.console.print_exception()
