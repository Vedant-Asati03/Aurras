from platform import system
from subprocess import CalledProcessError, run

from ..utils.logger import exception_log


WINDOWS = system() == "Windows"


def clear_screen():
    """
    Clears the terminal screen.
    """
    try:
        command = "cls" if WINDOWS else "clear"
        run(command, shell=True, check=True)
    except CalledProcessError as cpe:
        exception_log(cpe)
    except Exception as e:
        exception_log(f"an unknown error occured: {e}")
