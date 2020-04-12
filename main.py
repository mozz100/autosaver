import calendar
import datetime
import sys
from decimal import Decimal

if __name__ == "__main__":
    import settings
else:
    settings = object()


class Config:
    def __init__(self):
        for name, default in {
            "STARLING": {},
            "MONZO": {},
            "START_MONTH_WITH": Decimal("0.00"),
            "END_MONTH_WITH": Decimal("0.00"),
            "USE": "must set",
        }.items():
            value = getattr(settings, name, default)
            setattr(self, name, value)


config = Config()

TODAY = datetime.date.today()
FIRST_DAY = TODAY.replace(day=1)
DAYS_IN_MONTH = calendar.monthrange(FIRST_DAY.year, FIRST_DAY.month)[1]
LAST_DAY = FIRST_DAY.replace(day=DAYS_IN_MONTH)


def do_save():
    return input("Do this (enter y)? ").strip() == "y"


def main():
    if config.USE == "STARLING":
        from banks.starling import StarlingBank

        my_bank = StarlingBank(config.STARLING)
    elif config.USE == "MONZO":
        from banks.monzo import MonzoBank

        my_bank = MonzoBank(config.MONZO)
    else:
        print(f"Set config.USE to either MONZO or STARLING.")
        sys.exit(1)

    current_balance = my_bank.get_balance()
    gradient = (config.END_MONTH_WITH - config.START_MONTH_WITH) / DAYS_IN_MONTH
    ok_balance = round(gradient * TODAY.day + config.START_MONTH_WITH, 2)
    save = current_balance - ok_balance

    print(f"{FIRST_DAY} - {LAST_DAY}")
    print(f"Current balance: £{current_balance:.2f}")
    print(f"Spend rate: £{-gradient:.2f}/day")
    print(f"OK balance for today: £{ok_balance:.2f}")

    if save <= 0:
        print(f"No spare cash. £{-save:.2f} below OK.")
        sys.exit(0)

    goal_data = my_bank.get_goal_data()
    print(f"Looks like £{save:.2f} could be saved " + f" into '{goal_data['name']}'.")
    current = goal_data["balance"]
    target = goal_data["target"]
    prospective = current + save
    print(
        f"Target is £{target:.2f} - this would get from "
        f"£{current:.2f} ({round(100*current/target)}%) to "
        f"£{prospective:.2f} ({round(100*prospective/target)}%)."
    )

    if not do_save():
        print("No actions taken.")
        sys.exit(0)

    save_data = my_bank.save_goal(amount=save)

    if save_data["success"]:
        print("Done!")
        sys.exit(0)
    else:
        print("ERROR")
        print(save_data)
        sys.exit(1)


if __name__ == "__main__":
    main()
