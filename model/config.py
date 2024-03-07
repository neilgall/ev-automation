from dataclasses import dataclass
import datetime as dt


@dataclass
class Environment:
    cheap_rate_start: dt.time
    cheap_rate_end: dt.time


@dataclass
class Intent:
    max_grid_charge: int


@dataclass
class Status:
    now: dt.time
    battery_level: int
    estimated_range: int
    hvac_state: bool


@dataclass
class Config:
    max_solar: int


def get_config(env: Environment, intent: Intent, status: Status) -> Config:
    if status.battery_level >= intent.max_grid_charge:
        return Config(max_solar=100)

    if status.now < env.cheap_rate_start or env.cheap_rate_end < status.now:
        return Config(max_solar=100)

    return Config(max_solar=0)
