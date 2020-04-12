# copy this file to settings.py and fill in real values
from decimal import Decimal

START_MONTH_WITH = Decimal("500.00")
END_MONTH_WITH = Decimal("50.00")

# Starling
STARLING = {
    "PERSONAL_ACCESS_TOKEN": "x",  # obtain this from https://developer.starlingbank.com/personal/list
    "ACCOUNT_UUID": "y",  # get this from /api/v2/accounts
    "GOAL_UUID": "z",
}


# Monzo
# Visit https://developers.monzo.com/
MONZO = {
    "USER_ID": "x",
    "ACCOUNT_ID": "y",
    "POT_ID": "p",
    "POT_TARGET": Decimal(100.00),  # needs to be set here
    "CLIENT_SECRET": "s",
    "CLIENT_ID": "id",
    "REDIRECT_URI": "https://example.com",
}

USE = "STARLING"
