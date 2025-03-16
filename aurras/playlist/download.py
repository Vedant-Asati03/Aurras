from time import sleep
from pathlib import Path
from rich.console import Console

# Replace absolute import with relative import
from ..utils.path_manager import PathManager

_path_manager = PathManager()  # Create an instance to use

from ..core.downloader import SongDownloader
from ..playlist.manager import Select


class DownloadPlaylist:
    """
    Class for downloading playlists.
    """

    def __init__(self):
        """Initialize the DownloadPlaylist class."""
        self.console = Console()
        self.select_playlist = None
        self.downloaded_playlist_path = None
        self.download = None
        _path_manager.playlists_dir.mkdir(parents=True, exist_ok=True)

    def _get_playlist_from_db(self, playlist_name):
        self.select_playlist = Select()
        if playlist_name is None:
            self.select_playlist.select_playlist_from_db()
        elif "," in playlist_name:
            # If there are multiple playlists, take only the first one for now
            # (Multiple playlists should be handled by the caller)
            first_playlist = playlist_name.split(",")[0].strip()
            self.select_playlist.active_playlist = first_playlist
        else:
            self.select_playlist.active_playlist = playlist_name

    def _get_songs_from_active_playlist(self):
        self.select_playlist.songs_from_active_playlist()

    def _generate_download_playlist_path(self):
        """Generate the path for downloading the playlist and configure the downloader."""
        # Create a Path object for the playlist's directory
        self.downloaded_playlist_path = Path(
            _path_manager.playlists_dir, self.select_playlist.active_playlist.lower()
        )

        # Create the directory
        self.downloaded_playlist_path.mkdir(parents=True, exist_ok=True)

        # Initialize the downloader with the playlist songs and output directory
        self.download = SongDownloader(
            self.select_playlist.songs_in_active_playlist, self.downloaded_playlist_path
        )

    def download_playlist(self, playlist_name):
        """Download the specified playlist."""
        try:
            # Validate playlist name
            if playlist_name is None or playlist_name == "":
                self.console.print(
                    "[yellow]No playlist specified. Please select one.[/yellow]"
                )

            # Get the playlist data
            self._get_playlist_from_db(playlist_name)

            # Verify active playlist is set
            if not self.select_playlist.active_playlist:
                self.console.print(
                    "[bold red]No playlist selected or found.[/bold red]"
                )
                return

            self._get_songs_from_active_playlist()

            # Verify songs were found
            if not self.select_playlist.songs_in_active_playlist:
                self.console.print(
                    f"[yellow]Playlist '{self.select_playlist.active_playlist}' is empty. Nothing to download.[/yellow]"
                )
                return

            self._generate_download_playlist_path()

            self.console.print(
                f"Downloading Playlist - {self.select_playlist.active_playlist}\n\n",
                style="#D09CFA",
            )

            self.download.download_song()

            self.console.print("Download complete.", style="#D09CFA")
        except Exception as e:
            self.console.print(
                f"[bold red]Error downloading playlist: {str(e)}[/bold red]"
            )
