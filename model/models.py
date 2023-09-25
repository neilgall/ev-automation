from enum import Enum
from pydantic import BaseModel
from typing import Dict


class Intent(BaseModel):
    target_charge_car: int
    target_charge_house: int
    charge_car_first: bool


class ChargeState(BaseModel):
    current_charge_car: int
    current_charge_house: int
    

class CurrentPower(BaseModel):
    solar_watts: int
    battery_watts: int
    grid_import_watts: int
    grid_export_watts: int
    grid_offpeak: bool


class Configuration(BaseModel):
    target_charge_car: int
    target_charge_house: int
    house_charge_enable: bool
    house_charge_max_watts: int
    car_charge_enable: bool
    car_charge_max_solar: int


def determine_configuration(
    intent: Intent,
    state: ChargeState,
    power: CurrentPower
) -> Configuration:
    """
    Given an intended behaviour and the current state of the system
    determine the configuration required
    """
    car_needs_charge = state.current_charge_car < intent.target_charge_car
    car_can_charge = power.grid_offpeak or power.grid_export_watts >= 1400
    house_needs_charge = state.current_charge_house < intent.target_charge_house
    should_charge_car = car_needs_charge and car_can_charge and (intent.charge_car_first or not house_needs_charge)
    car_max_solar = 0 if power.grid_offpeak else 100

    return Configuration(
        target_charge_car = intent.target_charge_car,
        target_charge_house = intent.target_charge_house,
        house_charge_enable = not should_charge_car,
        house_charge_max_watts = 2600,
        car_charge_enable = should_charge_car,
        car_charge_max_solar = car_max_solar
    )
