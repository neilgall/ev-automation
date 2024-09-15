import datetime as dt
import pytest
from .environment import Environment


@pytest.mark.parametrize(
    "start_time,end_time,now,start,end",
    [
        # time in previous day
        (
            "00:00",
            "05:00",
            "2027-07-27T14:58:00.000",
            "2027-07-28T00:00:00.000",
            "2027-07-28T05:00:00.000",
        ),
        # at start or before cheap period
        (
            "00:30",
            "05:00",
            "2027-07-28T00:10:00.000",
            "2027-07-28T00:30:00.000",
            "2027-07-28T05:00:00.000",
        ),
        (
            "00:30",
            "05:00",
            "2027-07-28T00:30:00.000",
            "2027-07-28T00:30:00.000",
            "2027-07-28T05:00:00.000",
        ),
        (
            "00:00",
            "05:00",
            "2027-07-28T00:00:00.000",
            "2027-07-28T00:00:00.000",
            "2027-07-28T05:00:00.000",
        ),
        # during cheap period
        (
            "00:30",
            "05:00",
            "2027-07-28T01:10:00.000",
            "2027-07-28T00:30:00.000",
            "2027-07-28T05:00:00.000",
        ),
        (
            "00:30",
            "05:00",
            "2027-07-28T04:59:59.000",
            "2027-07-28T00:30:00.000",
            "2027-07-28T05:00:00.000",
        ),
        # after cheap period
        (
            "00:00",
            "05:00",
            "2027-07-27T05:00:00.000",
            "2027-07-28T00:00:00.000",
            "2027-07-28T05:00:00.000",
        ),
    ],
)
def test_next_cheap_rate_period(start_time, end_time, now, start, end):
    env = Environment(
        cheap_rate_start=dt.time.fromisoformat(start_time),
        cheap_rate_end=dt.time.fromisoformat(end_time),
        ready_by=dt.time(hour=9, minute=0),
        battery_capacity_kwh=0,
        charge_rate_kw=0,
    )
    now_dt = dt.datetime.fromisoformat(now)
    assert env.next_cheap_rate_start(now_dt) == dt.datetime.fromisoformat(start)
    assert env.next_cheap_rate_end(now_dt) == dt.datetime.fromisoformat(end)


@pytest.mark.parametrize(
    "capacity,rate,level,target_level,expect",
    [(100, 10, 0, 100, 600), (100, 10, 20, 80, 360), (60, 7.3, 0, 100, 493)],
)
def test_charge_minutes_needed(capacity, rate, level, target_level, expect):
    env = Environment(
        cheap_rate_start=dt.time(hour=0),
        cheap_rate_end=dt.time(hour=5),
        ready_by=dt.time(hour=9),
        battery_capacity_kwh=capacity,
        charge_rate_kw=rate,
    )
    assert env.charge_minutes_needed(level, target_level) == expect
