from dataclasses import dataclass
import datetime as dt


@dataclass
class Status:
    now: dt.time
    max_charge: int
    battery_level: int


@dataclass
class Config:
    max_solar: int


def get_config(status: Status) -> Config:
    if status.battery_level > status.max_charge:
        return Config(max_solar=100)

    if status.now < dt.time(hour=0, minute=30) or dt.time(hour=4, minute=30) < status.now:
        return Config(max_solar=100)

    return Config(max_solar=0)
