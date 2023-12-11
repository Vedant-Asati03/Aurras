import time
import platform
import subprocess
from rich.console import Console

from config import path
from lib.mpvsetup import mpv_setup
from lib.term_utils import clear_screen


class MPVPlayer:
    """
    A class representing an MPV player for playing media files.

    Attributes:
        console (Console): An instance of the rich Console class for console output.
        os_windows (bool): A boolean indicating whether the operating system is Windows.

    Methods:
        initialize_mpv()
            Initialize the MPV player by setting up the configuration files.

        generate_mpv_command(path_url: str) -> str:
            Generate an MPV command for the given path or URL.

        play(mpv_command: str)
            Play a media file using the MPV player.
    """

    def __init__(self):
        """
        Initialize the MPVPlayer class.
        """
        self.console = Console()
        self.os_windows = platform.system() == "Windows"

    @staticmethod
    def initialize_mpv():
        """
        Initialize mpv.conf and input.conf
        """
        mpv_setup()

    def generate_mpv_command(self, path_url: str):
        """Generate an MPV command for the given path or URL."""
        command = [
            "mpv",
            f"--include={path.mpv_conf}",
            f"--input-conf={path.input_conf}",
            path_url,
        ]

        return command

    def play(self, mpv_command: str, current_song: str):
        """
        Play a media file using the MPV player.

        Parameters:
            mpv_command (str): The command to play the media file with MPV.

        Raises:
            subprocess.CalledProcessError: If the MPV command execution fails.
        """
        clear_screen()
        self.console.print(
            f"Listening - {current_song}\n",
            end="\r",
            style="u #E8F3D6",
        )

        subprocess.run(
            mpv_command,
            check=True,
            shell=bool(self.os_windows),
        )
        clear_screen()


MPVPlayer.initialize_mpv()
