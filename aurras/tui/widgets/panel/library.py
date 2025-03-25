"""
Library panel widgets for Aurras TUI.
"""

from textual.containers import Vertical, VerticalScroll
from textual.widgets import OptionList

from ....utils.path_manager import PathManager
from ....playlist.manager import Select
from ..icon import Icon
from ..empty import Empty

_path_manager = PathManager()


class PlaylistsPanel(VerticalScroll):
    """Widget for displaying available playlists."""

    def __init__(self, *args, **kwargs):
        """Initialize the playlists panel."""
        super().__init__(*args, **kwargs)
        self.select = Select()
        self.border_title = "¹playlists"

    def compose(self):
        """Compose the playlists panel contents."""
        if self._load_saved_playlist():
            saved_playlists = OptionList(
                *self._load_saved_playlist(), id="saved-playlists-list"
            )
            saved_playlists.border_title = "saved"
            yield saved_playlists
        else:
            yield Empty("Nothing Found!", border_title="saved")

        if self._load_downloaded_playlists():
            downloaded_playlists = OptionList(
                *self._load_downloaded_playlists(), id="downloaded-playlists-list"
            )
            downloaded_playlists.border_title = "downloaded"
            yield downloaded_playlists
        else:
            yield Empty("Nothing Found!", border_title="downloaded")

    def _load_saved_playlist(self):
        """Load saved playlists from database."""
        playlists = self.select.load_playlist_from_db()
        return [f"{Icon.PRIMARY('')} {item}" for item in playlists]

    def _load_downloaded_playlists(self):
        """Load playlists into the panel."""
        playlists = _path_manager.list_directory(_path_manager.playlists_dir)
        return (
            [f"{Icon.PRIMARY('')} {item}" for item in playlists]
            if playlists
            else False
        )


class DownloadedTracksPanel(OptionList):
    """Widget for displaying downloaded tracks."""

    def __init__(self, *args, **kwargs):
        """Initialize the tracks panel."""
        super().__init__(*args, **kwargs)
        self.border_title = "²tracks"

    def compose(self):
        """Compose the tracks panel contents."""
        if not self._load_tracks():
            yield Empty()
            return
        self.add_options(self._load_tracks())

    def _load_tracks(self):
        """Load tracks into the panel."""
        tracks = _path_manager.list_directory(_path_manager.downloaded_songs_dir)
        return [f"{Icon.PRIMARY('')} {item}" for item in tracks] if tracks else None


class LibraryPanel(Vertical):
    """Container widget for library components (playlists and tracks)."""

    def __init__(self, *args, **kwargs):
        """Initialize the library panel."""
        super().__init__(*args, **kwargs)
        self.border_title = "Library"

    def compose(self):
        """Compose the library panel contents using the specialized widgets."""
        yield PlaylistsPanel(id="playlists-container")
        yield DownloadedTracksPanel(id="tracks-container")
