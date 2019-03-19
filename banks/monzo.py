import logging
import uuid
from decimal import Decimal

import requests

from .oauthbank import OAuthBank

MONZO_API = "https://api.monzo.com"
logger = logging.getLogger(__name__)


class MonzoBank(OAuthBank):
    def __init__(self, config):
        super().__init__(config)
        self.balance_url = f"{MONZO_API}/balance?account_id={self.config['ACCOUNT_ID']}"
        self.pots_url = f"{MONZO_API}/pots"
        self.configure_oauth(
            request_url="https://auth.monzo.com/",
            token_url="https://api.monzo.com/oauth2/token",
            refresh_url="https://api.monzo.com/oauth2/token",
        )
        self.session = self.get_authenticated_session()

    def _monzo_hit(self, method="get", **kwargs):
        """
        Make authenticated request to monzo API, return json result
        """
        mtd_call = getattr(self.session, method)
        resp = mtd_call(**kwargs)
        resp.raise_for_status()
        return resp.json()

    def get_balance(self):
        resp = self._monzo_hit(url=self.balance_url)
        return Decimal(resp["balance"]) / Decimal(100)

    def get_goal_data(self):
        # See https://docs.monzo.com/#pots
        resp = self._monzo_hit(url=self.pots_url)
        pot = [p for p in resp["pots"] if p["id"] == self.config["POT_ID"]][0]
        return {
            "name": pot["name"],
            "balance": pot["balance"] / Decimal(100.00),
            "target": self.config["POT_TARGET"],
        }

    def save_goal(self, amount):
        save_url = self.pots_url + "/" + self.config["POT_ID"] + "/deposit"
        try:
            resp = self._monzo_hit(
                url=save_url,
                method="put",
                data={
                    "source_account_id": self.config["ACCOUNT_ID"],
                    "amount": int(100 * amount),  # pence
                    "dedupe_id": str(uuid.uuid4()),
                },
            )
        except requests.exceptions.HTTPError as e:
            logger.exception("Failed saving to pot")
            return {"success": False}
        return {"success": resp["id"] == self.config["POT_ID"]}
