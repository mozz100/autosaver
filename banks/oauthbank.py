import json
import os
import uuid
from pathlib import Path

from requests_oauthlib import OAuth2Session

from .bank import Bank


class OAuthBank(Bank):
    @classmethod
    def get_token_filepath(cls):
        home = str(Path.home())
        return os.path.join(home, ".autosaver")

    @classmethod
    def save_token(cls, token):
        with open(OAuthBank.get_token_filepath(), "w") as fp:
            fp.write(
                json.dumps(
                    {
                        "about": "See https://github.com/mozz100/autosaver/",
                        "token": token,
                    }
                )
            )

    @classmethod
    def load_token(cls):
        try:
            with open(OAuthBank.get_token_filepath(), "r") as fp:
                return json.loads(fp.read())["token"]
        except FileNotFoundError:
            return None

    def configure_oauth(self, request_url, token_url, refresh_url):
        self.token_url = token_url
        self.refresh_url = refresh_url
        self.request_url = request_url
        self.client_id = self.config["CLIENT_ID"]
        self.client_secret = self.config["CLIENT_SECRET"]
        self.redirect_uri = self.config["REDIRECT_URI"]

    def get_authenticated_session(self):
        loaded_token = OAuthBank.load_token()
        if loaded_token:
            # so that if expires_at has passed, we auto-refresh
            loaded_token["expires_in"] = -10

            oauth = OAuth2Session(
                self.client_id,
                token=loaded_token,
                auto_refresh_url=self.refresh_url,
                auto_refresh_kwargs={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                token_updater=self.save_token,
            )
        else:
            oauth = OAuth2Session(self.client_id, redirect_uri=self.redirect_uri)
            authorization_url, state = oauth.authorization_url(
                self.request_url,
                # state is a Monzo-specific extra parameter.
                state=str(uuid.uuid4()),
            )
            print(
                f"Please go to the URL below and allow access.\n\n{authorization_url}\n\n"
            )
            authorization_response = input("Enter the full callback URL:\n\n")

            fetched_token = oauth.fetch_token(
                self.token_url,
                authorization_response=authorization_response,
                # Monzo specific extra parameter used for client
                # authentication
                client_secret=self.client_secret,
            )
            self.save_token(fetched_token)

        return oauth
