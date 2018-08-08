import urllib.parse
import json
from datetime import datetime, timezone, timedelta
import requests
import threading

from gogapi.base import ApiError
from gogapi import urls

GALAXY_ID = "46899977096215655"
GALAXY_SECRET = "9d85c43b1482497dbbce61f6e4aa173a433796eeae2ca8c5f6129f2dc4de46d9"

REDIRECT_URL = "https://embed.gog.com/on_login_success?origin=client"


def get_auth_url(client_id=GALAXY_ID):
    redirect_url_quoted = urllib.parse.quote(REDIRECT_URL)
    return urls.galaxy(
        "auth", client_id=client_id, redir_uri=redirect_url_quoted)


class Token:
    def __init__(self, client_id=GALAXY_ID, client_secret=GALAXY_SECRET):
        self.client_id = client_id
        self.client_secret = client_secret

        self.not_refreshing = threading.Event()
        self.not_refreshing.set()

    @classmethod
    def from_file(cls, filename):
        token = cls()
        token.load(filename)
        return token

    @classmethod
    def from_code(cls, login_code, client_id=GALAXY_ID, client_secret=GALAXY_SECRET):
        token_query = {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "authorization_code",
            "code": login_code,
            "redirect_uri": REDIRECT_URL # Needed for origin verification
        }
        token_resp = requests.get(urls.galaxy("token"), params=token_query)
        token = cls(client_id, client_secret)
        token.set_data(token_resp.json())
        return token

    def set_data(self, token_data):
        if "error" in token_data:
            raise ApiError(token_data["error"], token_data["error_description"])

        if "client_id" in token_data:
            self.client_id = token_data["client_id"]
        if "client_secret" in token_data:
            self.client_secret = token_data["client_secret"]
        self.access_token = token_data["access_token"]
        self.refresh_token = token_data["refresh_token"]
        self.expires_in = timedelta(seconds=token_data["expires_in"])
        self.scope = token_data["scope"]
        self.session_id = token_data["session_id"]
        self.token_type = token_data["token_type"]
        self.user_id = token_data["user_id"]
        if "created" in token_data:
            self.created = datetime.fromtimestamp(
                token_data["created"], tz=timezone.utc)
        else:
            self.created = datetime.now(tz=timezone.utc)

    def get_data(self):
        token_data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_in": int(self.expires_in.total_seconds()),
            "scope": self.scope,
            "session_id": self.session_id,
            "token_type": self.token_type,
            "user_id": self.user_id,
            "created": int(self.created.timestamp())
        }
        return token_data

    def load(self, filename):
        with open(filename, "r") as f:
            self.set_data(json.load(f))

    def save(self, filename):
        with open(filename, "w") as f:
            json.dump(self.get_data(), f, indent=2, sort_keys=True)

    def refresh(self, refresh_token=None):
        self.not_refreshing.clear()

        if refresh_token is None:
            refresh_token = self.refresh_token
        token_query = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
        token_resp = requests.get(urls.galaxy("token"), params=token_query)
        self.set_data(token_resp.json())
        self.not_refreshing.set()

    def expired(self, margin=timedelta(seconds=60)):
        self.not_refreshing.wait()
        expires_at = self.created + self.expires_in
        return (datetime.now(timezone.utc) - expires_at) > margin

    def __repr__(self):
        return str(self.__dict__)
