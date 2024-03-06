import datetime as dt
import pytest
from .config import Environment, Status, Intent, Config, get_config


def status(battery: int, now: str) -> Status:
    return Status(
        now=dt.time.fromisoformat(now),
        battery_level=battery
    )


@pytest.mark.parametrize("status,intent,config", [
    (status(50, "00:29"), Intent(60), Config(100)),
    (status(50, "00:30"), Intent(60), Config(0)),
    (status(50, "01:30"), Intent(60), Config(0)),
    (status(50, "02:30"), Intent(60), Config(0)),
    (status(50, "03:30"), Intent(60), Config(0)),
    (status(50, "04:30"), Intent(60), Config(0)),
    (status(50, "04:31"), Intent(60), Config(100)),
    (status(70, "01:30"), Intent(60), Config(100)),
    (status(50, "10:30"), Intent(80), Config(100))
])
def test_get_config(status: Status, intent: Intent, config: Config):
    env = Environment(
        cheap_rate_start = dt.time(hour=0, minute=30),
        cheap_rate_end = dt.time(hour=4, minute=30)
    )
    assert get_config(env, intent, status) == config
