from textual.app import App, ComposeResult
from textual_image.widget import Image, SixelImage

from textual.containers import Middle, Center


class ImageApp(App):

    CSS = """
    .image {
    height: 100%;
    width: 100%;
    }
"""

    def compose(self) -> ComposeResult:
        image = SixelImage(
            "C:\\Users\\vedan\\Wallpaper\\AOTWallpaper.jpg",
            classes="image",
        )
        yield (image)


ImageApp().run()
