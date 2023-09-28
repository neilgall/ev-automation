from pydantic import BaseModel


class Intent(BaseModel):
    target_charge_car: int
    target_charge_house: int
    charge_car_regardless: bool


class ChargeState(BaseModel):
    current_charge_car: int
    current_charge_house: int
    

class CurrentPower(BaseModel):
    solar_watts: int
    battery_watts: int
    consumption_watts: int
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

