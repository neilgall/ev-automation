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
class ChargeSchedule:
    start: dt.time
    end: dt.time


@dataclass
class Config:
    charge_from_grid: bool
    charge_schedule: ChargeSchedule | None


def get_config(env: Environment, intent: Intent, status: Status) -> Config:
    if status.battery_level >= intent.max_grid_charge:
        return Config(charge_from_grid=False, charge_schedule=None)

    if status.now < env.cheap_rate_start or env.cheap_rate_end < status.now:
        return Config(charge_from_grid=False, charge_schedule=None)

    return Config(
        charge_from_grid=True,
        charge_schedule=ChargeSchedule(
            start=env.cheap_rate_start,
            end=env.cheap_rate_end
        )
    )
