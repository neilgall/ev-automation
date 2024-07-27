import datetime as dt
import pytest
from .status import Status
from .intent import Intent
from .schedule import charge_schedule, ChargeSchedule
from .environment import Environment


@pytest.mark.parametrize("start_time,end_time,ready_by,now,battery,target,start,end", [
    # Charges which fit in the cheap period get scheduled for the whole period
    ("00:00", "05:00", "09:00", "2024-07-27T22:00:00.000", 20, 60, "2024-07-28T00:00:00.000", "2024-07-28T05:00:00.000"),
    ("00:30", "04:30", "09:00", "2024-07-28T01:00:00.000", 40, 60, "2024-07-28T00:30:00.000", "2024-07-28T04:30:00.000"),

    # Charges which take longer get extended at the end up to ready_by
    ("00:00", "05:00", "07:00", "2024-07-27T22:00:00.000", 20, 80, "2024-07-28T00:00:00.000", "2024-07-28T06:00:00.000"),
    ("00:00", "05:00", "07:01", "2024-07-27T22:00:00.000", 20, 90, "2024-07-28T00:00:00.000", "2024-07-28T07:00:00.000"),
    ("00:00", "05:00", "07:00", "2024-07-27T05:00:00.000", 70, 80, "2024-07-27T00:00:00.000", "2024-07-27T06:00:00.000"),

    # Charges which take even longer get extended before the cheap period too
    ("00:00", "05:00", "07:00", "2024-07-27T18:00:00.000", 10, 100, "2024-07-27T22:00:00.000", "2024-07-28T07:00:00.000")
])
def test_charge_schedule(start_time, end_time, ready_by, now, battery, target, start, end):
    env = Environment(
        cheap_rate_start=dt.time.fromisoformat(start_time),
        cheap_rate_end=dt.time.fromisoformat(end_time),
        ready_by=dt.time.fromisoformat(ready_by),
        battery_capacity_kwh=100,
        charge_rate_kw=10
    )
    intent = Intent(
        max_grid_charge=target
    )
    status = Status(
        now=dt.datetime.fromisoformat(now),
        battery_level=battery,
        estimated_range=0,
        hvac_state=False
    )
    schedule = charge_schedule(env, intent, status)
    assert schedule == ChargeSchedule(
        start=dt.datetime.fromisoformat(start),
        end=dt.datetime.fromisoformat(end)
    )
