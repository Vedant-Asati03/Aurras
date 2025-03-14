import platform
import subprocess
from rich.console import Console

# Replace absolute import with relative import
from ..utils.path_manager import PathManager

_path_manager = PathManager()  # Create an instance to use

from .setup import mpv_setup


class MPVPlayer:
    """
    A class representing an MPV player for playing media files.
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
            f"--include={_path_manager.mpv_conf}",
            f"--input-conf={_path_manager.input_conf}",
            path_url,
        ]

        return command

    def play(self, mpv_command: str, current_song: str):
        """
        Play a media file using the MPV player.

        Parameters:
            mpv_command (str): The command to play the media file with MPV.
            current_song (str): Name of the current song being played.

        Raises:
            subprocess.CalledProcessError: If the MPV command execution fails.
        """
        # Don't clear screen before playing - let the user see the queue info

        self.console.print(
            f"Listening - {current_song.capitalize()}\n",
            end="\r",
            style="u #E8F3D6",
        )

        try:
            subprocess.run(
                mpv_command,
                check=True,
                shell=bool(self.os_windows),
            )
            print(f"\nFinished playing: {current_song}")
        except subprocess.CalledProcessError as e:
            print(f"\nError playing {current_song}: {e}")
        except KeyboardInterrupt:
            print(f"\nPlayback of {current_song} stopped by user")

        # Don't clear screen after playing - we want to preserve output


MPVPlayer.initialize_mpv()
