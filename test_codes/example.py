# from textual.app import App
# from textual.color import Color
# from textual.widgets import Label
#
#
# class GradientApp(App):
#     CSS = """
#     .screen-gradient {
#         min-height: 0.165%;
#         height: 0.165%;
#         width: 100%;
#     }
#     """
#
#     def generate_gradient(self, start_color: str, end_color: str, num_steps: int = 1000, start_step: int = 385):
#         """Generates a gradient between two colors.
#
#         Args:
#             start_color (str): The starting color in hex or named color.
#             end_color (str): The ending color in hex or named color.
#             num_steps (int): Total number of gradient steps.
#             start_step (int): The step to start from (default is 385 for your example).
#         """
#         start_color = Color.parse(start_color)
#         end_color = Color.parse(end_color)
#
#         for i in range(start_step, num_steps + 1):
#             blend_ratio = i / num_steps
#             blended_color = start_color.blend(end_color, blend_ratio)
#             widget = Label(classes="screen-gradient")
#             widget.styles.background = blended_color
#             yield widget
#
#     def compose(self):
#         yield from self.generate_gradient("blue", "red")
#
#
# if __name__ == "__main__":
#     app = GradientApp()
#     app.run()


# from textual.app import App, ComposeResult
# from textual.widgets import Button, Label


# class QueryOneExampleApp(App):
#     def compose(self) -> ComposeResult:
#         # Add two widgets: a label and a button
#         yield Label("Initial Text", id="my_label")
#         yield Button("Click Me", id="my_button")

#     def on_button_pressed(self, event: Button.Pressed) -> None:
#         # Using query_one to find the label by its id and update its text
#         label = self.query_one(Label)
#         label.update("Button was clicked!")


# if __name__ == "__main__":
#     QueryOneExampleApp().run()



from textual.app import App
from textual.widgets import Input
from textual.suggester import Suggester

class SimpleSuggester(Suggester):
    async def get_suggestion(self, value: str) -> str | None:
        return f"Suggestion for {value}" if value else None

class SimpleApp(App):
    def compose(self):
        yield Input(suggester=SimpleSuggester())

if __name__ == "__main__":
    app = SimpleApp()
    app.run()