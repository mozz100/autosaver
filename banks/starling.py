from decimal import Decimal

import requests

from .bank import Bank

STARLING_API = "https://api.starlingbank.com/api/v2/"


class StarlingBank(Bank):
    def __init__(self, config):
        super().__init__(config)
        self.balance_url = (
            f"{STARLING_API}accounts/{self.config['ACCOUNT_UUID']}/balance"
        )
        self.goal_url = f"{STARLING_API}account/{self.config['ACCOUNT_UUID']}/savings-goals/{self.config['GOAL_UUID']}"

    def _starling_hit(self, method="get", **kwargs):
        """
        Make authenticated request to starling API, return json result
        """
        mtd_call = getattr(requests, method)
        resp = mtd_call(
            headers={
                "Authorization": f"Bearer {self.config['PERSONAL_ACCESS_TOKEN']}",
                "Content-Type": "application/json",
            },
            **kwargs,
        )
        resp.raise_for_status()
        return resp.json()

    def get_balance(self):
        balance_data = self._starling_hit(url=self.balance_url)

        return Decimal(balance_data["effectiveBalance"]["minorUnits"]) / Decimal(100)

    def get_goal_data(self):
        raw_data = self._starling_hit(url=self.goal_url)
        return {
            "name": raw_data["name"],
            "balance": raw_data["totalSaved"]["minorUnits"] / Decimal(100.00),
            "target": raw_data["target"]["minorUnits"] / Decimal(100.00),
        }

    def save_goal(self, amount):
        data = {"amount": {"currency": "GBP", "minorUnits": int(100 * amount)}}
        do_save_url = self.goal_url + "/add-money/" + self.get_unique_str()
        return self._starling_hit(method="put", url=do_save_url, json=data)
