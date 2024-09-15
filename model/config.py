from dataclasses import dataclass

from .environment import Environment
from .intent import Intent
from .schedule import charge_schedule, ChargeSchedule
from .status import Status


@dataclass
class Config:
    charge_from_grid: bool
    charge_schedule: ChargeSchedule | None


def get_config(env: Environment, intent: Intent, status: Status) -> Config:
    if status.battery_level >= intent.max_grid_charge:
        return Config(charge_from_grid=False, charge_schedule=None)

    schedule = charge_schedule(env, intent, status)
    print(f"schedule {schedule}")

    if status.now < schedule.start or schedule.end < status.now:
        return Config(charge_from_grid=False, charge_schedule=None)

    return Config(charge_from_grid=True, charge_schedule=schedule)
