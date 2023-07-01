import logging
from pathlib import Path
from datetime import date

# todo update logfile on day change if the app is still running


def get_logfile_path() -> Path:
    """
    Returns path to today's logfile.
    """
    filename = date.today()

    aurras_dir = Path.home() / ".aurras"
    logsdir: Path = aurras_dir / "logs"

    if not aurras_dir.exists():
        aurras_dir.mkdir()

    if not logsdir.exists():
        logsdir.mkdir()

    filepath: Path = logsdir / f"{filename}.log"

    if not filepath.exists():
        filepath.open('w').close()

    return filepath


# * setting this globally so that whenever this file is imported, logging config is set
logging.basicConfig(
    filename=get_logfile_path(), 
    level=logging.DEBUG, 
    format="%(asctime)s: %(message)s",
    datefmt="%H:%M:%S"
)


def log(message: str, level: str = "debug"):
    """
    Logs message with the given level to a file located in ~/.aurras/logs/{date}.log.
    """
    logging.debug(f"{message}\n")


if __name__ == "__main__":
    print(get_logfile_path())
    log("this is a test")