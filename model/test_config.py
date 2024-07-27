import datetime as dt
import pytest

from .environment import Environment
from .config import get_config
from .status import Status
from .intent import Intent


@pytest.mark.parametrize("start_time,end_time,ready_by,battery,target,now,charging", [
    # Charge from 00:00 to 04:00
    ("00:00", "05:00", "09:00", 20, 60, "2024-07-27T22:00:00.000", False),
    ("00:00", "05:00", "09:00", 20, 60, "2024-07-27T00:00:00.000", True),
    ("00:00", "05:00", "09:00", 30, 60, "2024-07-27T01:00:00.000", True),
    ("00:00", "05:00", "09:00", 40, 60, "2024-07-27T02:00:00.000", True),
    ("00:00", "05:00", "09:00", 50, 60, "2024-07-27T03:00:00.000", True),
    ("00:00", "05:00", "09:00", 60, 60, "2024-07-27T04:00:00.000", False),
    ("00:00", "05:00", "09:00", 60, 60, "2024-07-27T04:30:00.000", False),

    # Charge from 00:00 to 06:00
    ("00:00", "05:00", "07:00", 20, 80, "2024-07-27T22:00:00.000", False),
    ("00:00", "05:00", "09:00", 20, 80, "2024-07-27T00:00:00.000", True),
    ("00:00", "05:00", "09:00", 30, 80, "2024-07-27T01:00:00.000", True),
    ("00:00", "05:00", "09:00", 40, 80, "2024-07-27T02:00:00.000", True),
    ("00:00", "05:00", "09:00", 50, 80, "2024-07-27T03:00:00.000", True),
    ("00:00", "05:00", "09:00", 60, 80, "2024-07-27T04:00:00.000", True),
    ("00:00", "05:00", "09:00", 70, 80, "2024-07-27T05:00:00.000", True),
    ("00:00", "05:00", "09:00", 80, 80, "2024-07-27T06:00:00.000", False),

    # Charges which take even longer get extended before the cheap period too
    ("00:00", "05:00", "07:00", 10, 100, "2024-07-27T21:45:00.000", False),
    ("00:00", "05:00", "07:00", 10, 100, "2024-07-27T22:00:00.000", True),
    ("00:00", "05:00", "07:00", 30, 100, "2024-07-28T00:00:00.000", True),
    ("00:00", "05:00", "07:00", 50, 100, "2024-07-28T02:00:00.000", True),
    ("00:00", "05:00", "07:00", 70, 100, "2024-07-28T04:00:00.000", True),
    ("00:00", "05:00", "07:00", 90, 100, "2024-07-28T06:00:00.000", True),
    ("00:00", "05:00", "07:00", 99, 100, "2024-07-28T07:00:00.000", False),
])
def test_get_config(start_time, end_time, ready_by, battery, target, now, charging):
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
    config = get_config(env, intent, status)
    assert config.charge_from_grid == charging
