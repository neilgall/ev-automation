import datetime as dt
from dataclasses import dataclass


@dataclass
class Status:
    now: dt.datetime
    battery_level: int
    estimated_range: int
    hvac_state: bool
