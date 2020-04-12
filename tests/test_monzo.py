import tempfile
from unittest import mock

from banks.monzo import MonzoBank
from .utils import NetworkMockedTestCase, IntegrationTestCaseMixin, BankAPITestCaseMixin


@mock.patch(
    "banks.oauthbank.OAuthBank.load_token",
    return_value={"access_token": "yey", "expires_in": 3600},
)
@mock.patch("banks.oauthbank.OAuthBank.save_token")
class MonzoIntegrationTestCase(NetworkMockedTestCase, IntegrationTestCaseMixin):
    def setUp(self):
        super().setUp()
        self.config.USE = "MONZO"


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
        "banks.oauthbank.OAuthBank.get_token_filepath",
        return_value="test_data/token.json",
    )
    def test_existing_file(self, *m):
        with mock.patch("banks.oauthbank.OAuthBank.save_token", return_value=None):
            self.bank.get_authenticated_session()

    def test_save_token(self, *m):
        with tempfile.NamedTemporaryFile() as tf:
            with mock.patch(
                "banks.oauthbank.OAuthBank.get_token_filepath", return_value=tf.name
            ), mock.patch("banks.oauthbank.OAuthBank.load_token", return_value=None):
                self.bank.get_authenticated_session()
