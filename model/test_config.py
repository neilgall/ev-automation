import datetime as dt
import pytest
from .config import Environment, Status, Config, get_config


def status(limit: int, battery: int, now: str) -> Status:
    return Status(
        now=dt.time.fromisoformat(now),
        max_grid_charge=limit,
        battery_level=battery
    )


@pytest.mark.parametrize("status,config", [
    (status(60, 50, "00:29"), Config(100)),
    (status(60, 50, "00:30"), Config(0)),
    (status(60, 50, "01:30"), Config(0)),
    (status(60, 50, "02:30"), Config(0)),
    (status(60, 50, "03:30"), Config(0)),
    (status(60, 50, "04:30"), Config(0)),
    (status(60, 50, "04:31"), Config(100)),
    (status(60, 70, "01:30"), Config(100)),
    (status(80, 50, "10:30"), Config(100))
])
def test_get_config(status: Status, config: Config):
    env = Environment(
        cheap_rate_start = dt.time(hour=0, minute=30),
        cheap_rate_end = dt.time(hour=4, minute=30)
    )
    assert get_config(env, status) == config
