import datetime as dt
import pytest
from model import ChargeIntent, charge_intent, prune_charge_intent_dict


def test_charge_intent_for_today_actually_means_tomorrow_before_5am():
    intent = charge_intent(
        100, dt.date(2024, 8, 28), dt.datetime(2024, 8, 28, 17, 43, 0)
    )
    assert intent == ChargeIntent(100, dt.date(2024, 8, 29))


def test_charge_intent_for_today_means_today_before_5am():
    intent = charge_intent(
        100, dt.date(2024, 8, 28), dt.datetime(2024, 8, 28, 3, 43, 0)
    )
    assert intent == ChargeIntent(100, dt.date(2024, 8, 28))


@pytest.mark.parametrize(
    "future,now,result",
    [
        (
            dt.date(2024, 8, 29),
            dt.datetime(2024, 8, 28, 17, 45, 0),
            dt.date(2024, 8, 29),
        ),
        (
            dt.date(2024, 8, 29),
            dt.datetime(2024, 8, 28, 3, 45, 0),
            dt.date(2024, 8, 29),
        ),
        (
            dt.date(2024, 8, 31),
            dt.datetime(2024, 8, 28, 12, 0, 0),
            dt.date(2024, 8, 31),
        ),
    ],
)
def test_set_intent_for_future_date_sets_that_date(
    future: dt.date, now: dt.datetime, result: dt.date
):
    intent = charge_intent(100, future, now)
    assert intent == ChargeIntent(100, result)


def test_intent_updates_dict():
    intent = ChargeIntent(100, dt.date(2024, 8, 29))
    dict = intent.update_dict({"2024-03-01": 99})
    assert dict == {"2024-03-01": 99, "2024-08-29": 100}


def test_prune_removed_entries_before_today():
    intent = prune_charge_intent_dict(
        {
            "2024-03-01": 60,
            "2024-07-28": 100,
            "2024-08-29": 90,
            "2024-09-01": 80,
        },
        dt.datetime(2024, 8, 28, 12, 0, 0),
    )
    assert intent == {
        "2024-08-29": 90,
        "2024-09-01": 80,
    }
