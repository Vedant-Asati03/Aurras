from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from textual.widgets import Label, OptionList
from textual.containers import Center
from textual.widgets.option_list import Option, Separator


from config import path


class Downloads(Screen):
    directory = path.Config()
    CSS = """
    Screen {
        background: #2D3250;
        background-tint: #424769;
    }

    Label {
        align: center top;
        background: #2D3250;
        background-tint: #424769;
        border: round white;
        width: auto;
    }

    #no_downloaded_playlists {
        background: #2D3250;
        background-tint: #424769;
        width: auto;
    }
    """

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", priority=True),
    ]

    def compose(self) -> ComposeResult:
        yield Center(Label("Downloads"))

        for song in self.directory.list_directory(path.downloaded_songs):
            yield OptionList(Option(song))
        yield OptionList(Separator())

        # for playlist in self.directory.list_directory(path.downloaded_playlists):
        #     if playlist:
        #         yield OptionList(Option(playlist))
        #     else:
        #         yield label("No downloaded playlists found", id="no_downloaded_playlists")
