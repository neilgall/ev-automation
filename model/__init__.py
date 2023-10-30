from dataclasses import dataclass
from datetime import datetime, time
from typing import Optional


@dataclass
class Config:
    charge: bool
    max_solar: int


@dataclass
class Intent:
    charge_to: int
    charge_by: Optional[datetime]
    

@dataclass
class State:
    plugged_in: bool
    current_charge: int
    now: time
