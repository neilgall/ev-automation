from dataclasses import dataclass
import datetime as dt


@dataclass
class ChargeIntent:
    battery_percentage: int
    date: dt.date

    def update_dict(self, intent: dict[str, int]) -> dict[str, int]:
        intent[self.date.isoformat()] = self.battery_percentage
        return intent


def charge_intent(
    target_charge_level: int, target_charge_date: dt.date, now: dt.datetime
) -> ChargeIntent:
    if now.hour < 5:
        tomorrow = now.date()
    else:
        tomorrow = (now + dt.timedelta(days=1)).date()

    target_charge_date = max(target_charge_date, tomorrow)

    return ChargeIntent(target_charge_level, target_charge_date)


def prune_charge_intent_dict(
    intent: dict[str, int], now: dt.datetime
) -> dict[str, int]:
    today = now.date()

    def expired(date):
        try:
            date = dt.date.fromisoformat(date)
            return date < today
        except:
            return True

    return {(date): charge for date, charge in intent.items() if not expired(date)}
