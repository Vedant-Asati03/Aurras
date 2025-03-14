import questionary
from ...ui.command_palette import UpdateSpecifiedSettings
from ...utils.terminal import clear_screen
from .database import SpotifyDatabase
from .connection import SetupSpotifyConnection


class CheckSpotifyAuthenticationStatus:
    def __init__(self) -> None:
        self.response = None
        self.spotify_conn = None
        self.update_authentication_status = UpdateSpecifiedSettings("authenticated")
        self.setup_spotify_connection = SetupSpotifyConnection()
        self.spotify_db = SpotifyDatabase()

    def _get_response(self):
        clear_screen()
        template = (
            "🎵 **Enhance Your Aurras Experience!** 🎵\n\n"
            "Authenticate with Spotify to unlock:\n"
            "• **Highly personalized** song recommendations 🤩\n"
            "• **Direct access** to your Spotify playlists from Aurras 🙌\n\n"
            "This will only take a few easy steps. Would you like to proceed?\n"
        )

        choices = ["Yes", "Not now!", "I dont use Spotify"]

        self.response = questionary.select(message=template, choices=choices).ask()

    def _update_authenticated_settings(self, status: str):
        self.update_authentication_status.update_specified_setting_directly(status)

    def _if_not_authenticated_then_authenticate(self):
        self.spotify_db.setup_auth_db()
        self._update_authenticated_settings("yes")

    def check_if_authenticated(self):
        try:
            self.setup_spotify_connection.create_spotify_connection()
            self.spotify_conn = self.setup_spotify_connection.spotify_conn
            self._update_authenticated_settings("yes")

        except Exception:
            self._get_response()

            match self.response:
                case "Yes":
                    self._if_not_authenticated_then_authenticate()

                case _:
                    self._update_authenticated_settings("no")
