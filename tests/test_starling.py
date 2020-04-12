from banks.starling import StarlingBank
from .utils import NetworkMockedTestCase, IntegrationTestCaseMixin, BankAPITestCaseMixin


class StarlingIntegrationTestCase(NetworkMockedTestCase, IntegrationTestCaseMixin):
    def setUp(self):
        super().setUp()
        self.config.USE = "STARLING"


class StarlingAPITestCase(NetworkMockedTestCase, BankAPITestCaseMixin):
    def setUp(self):
        super().setUp()
        self.bank = StarlingBank(self.config.STARLING)
