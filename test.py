import re
import tempfile
from decimal import Decimal
from unittest import TestCase, mock

import requests_mock

import main
from banks.bank import Bank
from banks.monzo import MonzoBank
from banks.starling import StarlingBank


class NetworkMockedTestCase(TestCase):
    ACCOUNT_UUID = "135cacf6-2ff2-452e-acfd-c3c6588f5987"
    GOAL_UUID = "21070d5a-1097-40fe-b4df-763a888d53ce"
    RAND_UUID = "f0311f2e-ce10-43f0-914b-f4911c22a0e5"

    USER_ID = "userid"
    ACCOUNT_ID = "acc_accountid"
    ACCESS_TOKEN = "token"
    POT_ID = "pot_0000"

    def setUp(self):
        self.requests_mocker = requests_mock.mock()

        # Balance £9,999
        self.balance = 9999
        self.requests_mocker.get(
            f"https://api.starlingbank.com/api/v2/accounts/{NetworkMockedTestCase.ACCOUNT_UUID}/balance",
            json={"effectiveBalance": {"minorUnits": 100 * self.balance}},  # pence
        )
        self.requests_mocker.get(
            f"https://api.monzo.com/balance?account_id={NetworkMockedTestCase.ACCOUNT_ID}",
            json={"balance": 100 * self.balance},  # pence
        )

        # Goal retrieve.  £99 in pot/goal
        self.goal_balance = 99
        self.goal_target = 333
        self.requests_mocker.get(
            f"https://api.starlingbank.com/api/v2/account/{NetworkMockedTestCase.ACCOUNT_UUID}/savings-goals/{NetworkMockedTestCase.GOAL_UUID}",
            json={
                "name": "My goal",
                "totalSaved": {"minorUnits": 100 * self.goal_balance},  # pence
                "target": {"minorUnits": 100 * self.goal_target},  # pence
            },
        )
        self.requests_mocker.get(
            f"https://api.monzo.com/pots",
            json={
                "pots": [
                    {
                        "id": NetworkMockedTestCase.POT_ID,
                        "name": "My goal",
                        "style": "beach_ball",
                        "balance": 100 * self.goal_balance,
                        "currency": "GBP",
                        "created": "2017-11-09T12:30:53.695Z",
                        "updated": "2017-11-09T12:30:53.695Z",
                        "deleted": False,
                    }
                ]
            },
        )

        # Goal/pot save up.
        self.requests_mocker.put(
            f"https://api.starlingbank.com/api/v2/account/{NetworkMockedTestCase.ACCOUNT_UUID}/savings-goals/{NetworkMockedTestCase.GOAL_UUID}/add-money/{NetworkMockedTestCase.RAND_UUID}",
            json={"success": True},
        )
        self.requests_mocker.put(
            f"https://api.monzo.com/pots/{NetworkMockedTestCase.POT_ID}/deposit",
            json={
                "id": NetworkMockedTestCase.POT_ID,
                "name": "Wedding Fund",
                "style": "beach_ball",
                "balance": 550_100,
                "currency": "GBP",
                "created": "2017-11-09T12:30:53.695Z",
                "updated": "2018-02-26T07:12:04.925Z",
                "deleted": False,
            },
        )

        # Oauth
        self.requests_mocker.post(
            "https://api.monzo.com/oauth2/token",
            json={"access_token": "a", "expires_in": 3600},
        )

        self.requests_mocker.start()

        # Testing config
        self.config = main.config
        self.config.STARLING = {
            "ACCOUNT_UUID": NetworkMockedTestCase.ACCOUNT_UUID,
            "GOAL_UUID": NetworkMockedTestCase.GOAL_UUID,
            "PERSONAL_ACCESS_TOKEN": "xyz",
        }
        self.config.MONZO = {
            "USER_ID": NetworkMockedTestCase.USER_ID,
            "ACCOUNT_ID": NetworkMockedTestCase.ACCOUNT_ID,
            "POT_ID": NetworkMockedTestCase.POT_ID,
            "POT_TARGET": Decimal(self.goal_target),
            "CLIENT_ID": "client_id",
            "CLIENT_SECRET": "client_secret",
            "REDIRECT_URI": "https://example.com",
        }
        self.config.START_MONTH_WITH = Decimal("250.00")
        self.config.END_MONTH_WITH = Decimal("50.00")


@mock.patch("main.print")
class IntegrationTestCaseMixin:
    def test_no_USE(self, *m):
        self.config.USE = ""
        with self.assertRaises(SystemExit) as sysexit:
            main.main()
        self.assertEqual(1, sysexit.exception.code)

    @mock.patch("main.input", return_value="n")
    def test_main_no_save(self, *m):
        with self.assertRaises(SystemExit) as sysexit:
            main.main()
        self.assertEqual(0, sysexit.exception.code)

    @mock.patch("main.input", return_value="y")
    @mock.patch("banks.bank.uuid.uuid4", return_value=NetworkMockedTestCase.RAND_UUID)
    def test_main_save(self, *m):
        with self.assertRaises(SystemExit) as sysexit:
            main.main()
        self.assertEqual(0, sysexit.exception.code)

    @mock.patch("main.input", return_value="y")
    @mock.patch("banks.bank.uuid.uuid4", return_value=NetworkMockedTestCase.RAND_UUID)
    @mock.patch("banks.monzo.logger")
    def test_main_save_fails(self, *m):
        self.requests_mocker.put(
            f"https://api.starlingbank.com/api/v2/account/{NetworkMockedTestCase.ACCOUNT_UUID}/savings-goals/{NetworkMockedTestCase.GOAL_UUID}/add-money/{NetworkMockedTestCase.RAND_UUID}",
            json={"success": False},
        )
        self.requests_mocker.put(
            f"https://api.monzo.com/pots/{NetworkMockedTestCase.POT_ID}/deposit",
            json={"success": False},
            status_code=503,
        )
        with self.assertRaises(SystemExit) as sysexit:
            main.main()
        self.assertEqual(1, sysexit.exception.code)

    def test_main_no_spare_cash(self, *m):
        self.requests_mocker.get(
            f"https://api.starlingbank.com/api/v2/accounts/{NetworkMockedTestCase.ACCOUNT_UUID}/balance",
            json={"effectiveBalance": {"minorUnits": 1}},
        )
        self.requests_mocker.get(
            f"https://api.monzo.com/balance?account_id={NetworkMockedTestCase.ACCOUNT_ID}",
            json={
                "id": NetworkMockedTestCase.POT_ID,
                "name": "Wedding Fund",
                "style": "beach_ball",
                "balance": 1,
                "currency": "GBP",
                "created": "2017-11-09T12:30:53.695Z",
                "updated": "2018-02-26T07:12:04.925Z",
                "deleted": False,
            },
        )

        with self.assertRaises(SystemExit) as sysexit:
            main.main()
        self.assertEqual(0, sysexit.exception.code)


class StarlingIntegrationTestCase(NetworkMockedTestCase, IntegrationTestCaseMixin):
    def setUp(self):
        super().setUp()
        self.config.USE = "STARLING"


@mock.patch(
    "banks.oauthbank.OAuthBank.load_token",
    return_value={"access_token": "yey", "expires_in": 3600},
)
@mock.patch("banks.oauthbank.OAuthBank.save_token")
class MonzoIntegrationTestCase(NetworkMockedTestCase, IntegrationTestCaseMixin):
    def setUp(self):
        super().setUp()
        self.config.USE = "MONZO"


class BankAPITestCaseMixin:
    @mock.patch("banks.bank.uuid.uuid4", return_value=NetworkMockedTestCase.RAND_UUID)
    def test_str(self, *m):
        self.assertEqual(NetworkMockedTestCase.RAND_UUID, self.bank.get_unique_str())

    def test_balance(self, *m):
        retrieved_balance = self.bank.get_balance()
        self.assertIsInstance(retrieved_balance, Decimal)
        self.assertAlmostEqual(self.balance, float(retrieved_balance))

    def test_goal_data(self, *m):
        retrieved_goal_data = self.bank.get_goal_data()
        self.assertIsInstance(retrieved_goal_data, dict)

        self.assertIsInstance(retrieved_goal_data["balance"], Decimal)
        self.assertAlmostEqual(self.goal_balance, float(retrieved_goal_data["balance"]))

        self.assertIsInstance(retrieved_goal_data["target"], Decimal)
        self.assertAlmostEqual(self.goal_target, float(retrieved_goal_data["target"]))

        self.assertIsInstance(retrieved_goal_data["name"], str)

    @mock.patch("banks.bank.uuid.uuid4", return_value=NetworkMockedTestCase.RAND_UUID)
    def test_save_goal(self, *m):
        save_goal_data = self.bank.save_goal(amount=Decimal("1.00"))
        self.assertTrue(save_goal_data["success"])


class StarlingAPITestCase(NetworkMockedTestCase, BankAPITestCaseMixin):
    def setUp(self):
        super().setUp()
        self.bank = StarlingBank(self.config.STARLING)


@mock.patch("banks.oauthbank.input", return_value="https://example.com?code=c&state=x")
@mock.patch("banks.oauthbank.print")
class MonzoAPITestCase(NetworkMockedTestCase, BankAPITestCaseMixin):
    @mock.patch(
        "banks.oauthbank.OAuthBank.load_token",
        return_value={"access_token": "yey", "expires_in": 3600},
    )
    @mock.patch("banks.oauthbank.OAuthBank.save_token")
    def setUp(self, *m):
        super().setUp()
        self.bank = MonzoBank(self.config.MONZO)

    @mock.patch("banks.oauthbank.OAuthBank.save_token")
    def test_no_saved_token(self, *m):
        with mock.patch("banks.oauthbank.OAuthBank.load_token", return_value=None):
            self.bank.get_authenticated_session()

    def test_get_token_filepath(self, *m):
        self.assertIsInstance(self.bank.get_token_filepath(), str)

    @mock.patch(
        "banks.oauthbank.OAuthBank.get_token_filepath", side_effect=FileNotFoundError()
    )
    @mock.patch("banks.oauthbank.print")
    def test_no_file(self, *m):
        with mock.patch("banks.oauthbank.OAuthBank.save_token", return_value=None):
            self.bank.get_authenticated_session()

    @mock.patch(
        "banks.oauthbank.OAuthBank.get_token_filepath", return_value="test_data/token.json"
    )
    def test_existing_file(self, *m):
        with mock.patch("banks.oauthbank.OAuthBank.save_token", return_value=None):
            self.bank.get_authenticated_session()

    def test_save_token(self, *m):
        with tempfile.NamedTemporaryFile() as tf:
            with mock.patch(
                "banks.oauthbank.OAuthBank.get_token_filepath", return_value=tf.name
            ), mock.patch(
                "banks.oauthbank.OAuthBank.load_token",
                return_value=None,
            ):
                self.bank.get_authenticated_session()
