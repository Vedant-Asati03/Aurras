from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.color import Color
from textual.suggester import Suggester
from textual.widgets import (
    Header,
    Footer,
    Label,
    Input,
    Button,
    ProgressBar,
)
from textual.containers import (
    VerticalScroll,
    Container,
    Horizontal,
    Grid,
)
from textual.binding import Binding
from textual.reactive import reactive
from textual_image.widget import Image

from lib.manage_song_searches.handle_song_searches.search_on_youtube import (
    SearchFromYoutube,
)
from pages.downloads import Downloads


class InSearchRecommendation(Suggester):

    async def get_suggestion(self, value: str) -> str | None:
        """Generate suggestions based on the current input value."""
        if not value:
            return None

        search_song = SearchFromYoutube(value)
        try:
            search_song.search_from_youtube()
        except Exception:
            return None

        song_recommendation = search_song.song_metadata.song_name_searched
        return song_recommendation


class Playlist(Screen):
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", priority=True),
    ]

    def compose(self) -> ComposeResult:
        yield Label("Songs")


class Lyrics(Screen):
    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", priority=True),
    ]

    def compose(self) -> ComposeResult:
        yield Label("Lyrics")


class Aurras(App):
    COMMAND_PALETTE_BINDING = "ctrl+@"

    CSS_PATH = "css.tcss"
    SCREENS = {"playlist": Playlist}

    BINDINGS = [
        Binding("ctrl+h", "", "Help", priority=True),
        Binding("q", "quit", "Quit", show=False, priority=True),
        Binding("up", "increase_vol", "Increase Volume", show=False, priority=True),
        Binding("down", "decrease_vol", "Decrease Volume", show=False, priority=True),
    ]

    volume_icon = reactive("")

    def __init__(self):
        self.ls = [
            "Playlist 1",
            "Playlist 2",
            "Playlist 3",
            "Playlist 4",
            "Playlist 5",
            "Playlist 6",
            "Playlist 7",
            "Playlist 8",
            "Playlist 9",
            "Playlist 10",
        ]
        self.volume_bar = ProgressBar(
            total=10, show_eta=False, show_percentage=False, classes="volume-bar"
        )
        self.volume = 120
        super().__init__()

    def compose(self) -> ComposeResult:
        time_stamp = "0:00"
        song_duration = "3:00"

        with Container(classes="home-page"):
            yield Horizontal(
                Input(
                    placeholder="  Search...",
                    suggester=InSearchRecommendation(),
                    classes="search-bar",
                ),
                Button(
                    "", tooltip="Downloads", classes="button downloads", id="downloads"
                ),
                classes="top-pane",
            )
            yield Grid(
                Button("placeholder", classes="button card"),
                Button("Discover", classes="button card"),
                Button("Liked Songs  ", classes="button card"),
                Button("Recent Songs", classes="button card"),
                classes="card-grid",
            )

        with VerticalScroll(
            Label("Playlists", classes="left-pane-scrollable-title"),
            classes="left-pane-scrollable",
        ):
            for index, playlist in enumerate(self.ls):
                yield Button(label=playlist, classes="song-button", id=f"pl{index}")

        yield Image("C:\\Users\\vedan\\Wallpaper\\AOTWallpaper.jpg",
            classes="album-cover",
        )
        yield Grid(
            Horizontal(
                Button("󰃂", tooltip="Bookmark", classes="button bookmark"),
                Button("󰒮", tooltip="Previous", classes="button previous-track"),
                Button("", tooltip="Play/ Pause", classes="button play"),
                Button("󰒭", tooltip="Next", classes="button next-track"),
                Button("", tooltip="Loop", classes="button loop"),
                classes="music-control",
            ),
            Horizontal(
                Button("", tooltip="Add to liked Songs", classes="button like-song"),
                Label("Song Name", classes="display-active-song"),
                Label(time_stamp, classes="display-song-time-stamp"),
                ProgressBar(
                    total=100,
                    classes="progress-bar",
                    show_eta=False,
                    show_percentage=False,
                ),
                Label(song_duration, classes="display-song-duration"),
                Button("", tooltip="Lyrics", classes="button lyrics", id="lyrics"),
                Button("󰼄", tooltip="Queue", classes="button queue"),
                Label(self.volume_icon, classes="volume-icon", id="vol_icon"),
                self.volume_bar,
                Button("", tooltip="Immersive View", classes="button immersive-view"),
                classes="song-playing-info",
            ),
            classes="bottom-pane",
        )

        # self._check_vol()

        yield Header()
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "lyrics":
            self.push_screen(Lyrics())
        elif event.button.id == "downloads":
            self.push_screen(Downloads())
        elif event.button.id == "pl0":
            self.push_screen(Playlist())

    def on_mount(self) -> None:
        self.query_one(ProgressBar).update(progress=100)

    def _check_vol(self):
        if self.volume == 0:
            self.query_one("#vol_icon", Label).volume_icon = ""
        elif self.volume <= 60:
            self.query_one("#vol_icon", Label).volume_icon = ""

    def action_increase_vol(self) -> None:
        """Increase the progress when up arrow is pressed."""
        if self.volume <= 10:
            self.volume += 1
            self.volume_bar.advance(1)

    def action_decrease_vol(self) -> None:
        """Decrease the progress when down arrow is pressed."""
        if self.volume >= 0:
            self.volume -= 1
            self.volume_bar.advance(-1)

    def generate_gradient(
        self,
        start_color: str,
        end_color: str,
        num_steps: int = 1000,
        start_step: int = 0,
    ):
        start_color = Color.parse(start_color)
        end_color = Color.parse(end_color)

        for i in range(start_step, num_steps + 1):
            blend_ratio = i / num_steps
            blended_color = start_color.blend(end_color, blend_ratio)
            widget = Label(classes="screen-gradient")
            widget.styles.background = blended_color
            yield widget


if __name__ == "__main__":
    Aurras().run()
