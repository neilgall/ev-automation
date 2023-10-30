from dataclasses import dataclass


@dataclass
class Config:
    charge: bool
    max_solar: int
