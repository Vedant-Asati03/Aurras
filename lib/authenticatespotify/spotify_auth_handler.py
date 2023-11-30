import sqlite3
import questionary
import spotipy
from spotipy import util

import config.config as path
from src.command_palette.command_palette_config import UpdateSpecifiedSettings
from lib.term_utils import clear_screen
from lib.authenticatespotify.spotify_database_handler import SpotifyDatabase


class SpotifyConnectionStatus:
    def __init__(self) -> None:
        self.spotify_conn = None
        self.spotify_db = SpotifyDatabase()


class SpotifyCredentialsManager(SpotifyConnectionStatus):
    def __init__(self) -> None:
        super().__init__()
        self.client_id = None
        self.client_secret = None
        self.scope = None
        self.username = None
        self.redirect_uri = None

    def _fetch_auth_credentials_from_db(self):
        with sqlite3.connect(path.spotify_auth) as auth:
            cursor = auth.cursor()
            cursor.execute(
                "SELECT client_id, client_secret, scope, username, redirect_uri FROM spotify_auth"
            )
            credentials = cursor.fetchone()

        self.client_id = credentials[0]
        self.client_secret = credentials[1]
        self.scope = credentials[2]
        self.username = credentials[3]
        self.redirect_uri = credentials[4]

    def spotify_connection(self):
        self._fetch_auth_credentials_from_db()

        token = util.prompt_for_user_token(
            client_id=self.client_id,
            client_secret=self.client_secret,
            scope=self.scope,
            username=self.username,
            redirect_uri=self.redirect_uri,
        )

        self.spotify_conn = spotipy.Spotify(auth=token)


class SpotifyAuthHandler:
    def __init__(self) -> None:
        self.response = None
        self.update_authentication_status = UpdateSpecifiedSettings("authenticated")
        self.spotify_credentials = SpotifyCredentialsManager()
        self.spotify_db = SpotifyDatabase()

    def _get_response(self):
        clear_screen()

        template = (
            "Improve your experience with Aurras. "
            "Please authenticate yourself with Spotify\n"
            "This will only take a few easy steps\n"
            "To enable features like-\n"
            "• Highly personalised🤩 song recommendations\n"
            "• Access to your Spotify playlists directly from Aurras🙌.\n\n"
        )
        choices = ["Yes", "Not now!", "I dont use Spotify"]

        self.response = questionary.select(message=template, choices=choices).ask()

    def _if_not_authenticated_then_authenticate(self):
        self.spotify_db.setup_auth_db()
        self._update_authenticated_settings()

    def _update_authenticated_settings(self):
        self.update_authentication_status.update_specified_setting_directly("true")

    def check_if_authenticated(self):
        try:
            self.spotify_credentials.spotify_connection()
            self._update_authenticated_settings()

        except Exception:
            self._get_response()

            match self.response:
                case "Yes":
                    self._if_not_authenticated_then_authenticate()

                case _:
                    self.update_authentication_status.update_specified_setting_directly(
                        "false"
                    )
