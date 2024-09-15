import datetime as dt
from dataclasses import dataclass

from .status import Status
from .intent import Intent
from .environment import Environment


@dataclass
class ChargeSchedule:
    start: dt.datetime
    end: dt.datetime


def charge_schedule(env: Environment, intent: Intent, status: Status) -> ChargeSchedule:
    if env.cheap_rate_start < status.now.time() < env.cheap_rate_end:
        return ChargeSchedule(
            start=env.next_cheap_rate_start(status.now),
            end=env.next_cheap_rate_end(status.now),
        )

    minutes_needed = env.charge_minutes_needed(
        status.battery_level, intent.max_grid_charge
    )
    if env.cheap_rate_end <= status.now.time() < env.ready_by:
        predicted_end = status.now + dt.timedelta(minutes=minutes_needed)
        return ChargeSchedule(
            start=dt.datetime.combine(status.now.date(), env.cheap_rate_start),
            end=predicted_end,
        )

    if minutes_needed > env.cheap_rate_duration_minutes:
        start = env.next_cheap_rate_start(status.now)
        end = start + dt.timedelta(minutes=minutes_needed)
        ready_by = env.next_ready_by(status.now)
        if end < ready_by:
            return ChargeSchedule(start, end)
        else:
            return ChargeSchedule(
                start=ready_by - dt.timedelta(minutes=minutes_needed), end=ready_by
            )

    return ChargeSchedule(
        start=env.next_cheap_rate_start(status.now),
        end=env.next_cheap_rate_end(status.now),
    )
