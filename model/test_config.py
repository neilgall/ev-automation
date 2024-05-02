import datetime as dt
import pytest
from .config import Environment, Status, Intent, Config, ChargeSchedule, get_config


offpeak = ChargeSchedule(
    start = dt.time(hour=0, minute=30),
    end = dt.time(hour=4, minute=30)
)


def status(battery: int, now: str) -> Status:
    return Status(
        now=dt.time.fromisoformat(now),
        battery_level=battery,
        estimated_range=0,
        hvac_state=False
    )


@pytest.mark.parametrize("status,intent,config", [
    (status(50, "00:29"), Intent(60), Config(False, None)),
    (status(50, "00:30"), Intent(60), Config(True, offpeak)),
    (status(50, "01:30"), Intent(60), Config(True, offpeak)),
    (status(50, "02:30"), Intent(60), Config(True, offpeak)),
    (status(50, "03:30"), Intent(60), Config(True, offpeak)),
    (status(50, "04:30"), Intent(60), Config(True, offpeak)),
    (status(50, "04:31"), Intent(60), Config(False, None)),
    (status(70, "01:30"), Intent(60), Config(False, None)),
    (status(50, "10:30"), Intent(80), Config(False, None))
])
def test_get_config(status: Status, intent: Intent, config: Config):
    env = Environment(
        cheap_rate_start = dt.time(hour=0, minute=30),
        cheap_rate_end = dt.time(hour=4, minute=30)
    )
    assert get_config(env, intent, status) == config
