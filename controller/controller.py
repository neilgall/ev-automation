from services.andersen import AndersenA2
from services.givenergy import GivEnergy
from renault_api.renault_vehicle import RenaultVehicle
from model import CurrentPower, ChargeState, Configuration


class Controller:
    def __init__(
        self, *,
        givenergy: GivEnergy,
        andersen: AndersenA2,
        vehicle: RenaultVehicle
    ):
        self._givenergy = givenergy
        self._andersen = andersen
        self._vehicle = vehicle


    async def charge_state(self) -> ChargeState:
        """
        Read the current ChargeState
        """
        car_battery_status = await self._vehicle.get_battery_status()
        return ChargeState(
            current_charge_car = car_battery_status.batteryLevel,
            current_charge_house = self._givenergy.current_charge()
        )

    async def current_power(self) -> CurrentPower:
        """
        Read the current power levels
        """
        return CurrentPower(
            solar_watts = self._givenergy.solar_watts(),
            battery_watts = self._givenergy.battery_watts(),
            grid_import_watts = self._givenergy.grid_import_watts(),
            grid_export_watts = self._givenergy.grid_export_watts(),
            grid_offpeak = self._givenergy.grid_offpeak()
        )

    def apply_configuration(self, config: Configuration):
        """
        Apply a Configuration
        """
        if config.house_charge_enable:
            self._givenergy.enable_charge_target(config.target_charge_house)
            self._givenergy.enable_charge()
            self._givenergy.disable_discharge()
            self._andersen.disable_charge()

        elif config.car_charge_enable:
            self._givenergy.disable_charge()
            self._givenergy.disable_discharge()
            self._andersen.set_max_solar(config.car_charge_max_solar)
            self._andersen.enable_charge()
        
        else:
            self._givenergy.enable_charge()
            self._givenergy.enable_discharge()
            self._andersen.disable_charge()
