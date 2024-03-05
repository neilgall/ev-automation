import datetime as dt
import pytest
from .config import Status, Config, get_config


def status(limit: int, battery: int, now: str) -> Status:
    return Status(
        now=dt.time.fromisoformat(now),
        max_charge=limit,
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
    assert get_config(status) == config
