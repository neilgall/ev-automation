from dataclasses import dataclass
from datetime import time
from typing import Optional


@dataclass
class Config:
    charge: bool
    max_solar: int


@dataclass
class Intent:
    charge_to: int
    offpeak_only: bool


@dataclass
class State:
    current_charge: int
    now: time
