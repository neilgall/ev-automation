import logging
import sys
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from services.andersen import AndersenA2
from services.givenergy import GivEnergy
from renault_api.renault_vehicle import RenaultVehicle
from model import Intent, CurrentPower, ChargeState, Configuration
from model.statemachine import StateMachine


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(handler)


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
        self._intent = Intent(target_charge_car=80, target_charge_house=100, charge_car_regardless=False)
        self._statemachine = StateMachine()
        self._scheduler = AsyncIOScheduler()
        self._monitor_job = self._scheduler.add_job(self._monitor, "interval", seconds=30)
        self._scheduler.start()
        logger.info("Controller started")

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
            consumption_watts = self._givenergy.consumption_watts(),
            grid_import_watts = self._givenergy.grid_import_watts(),
            grid_export_watts = self._givenergy.grid_export_watts(),
            grid_offpeak = self._givenergy.grid_offpeak()
        )

    async def _monitor(self):
        """
        Periodic monitor
        """
        config = self._statemachine.update(
            self._intent,
            await self.charge_state(),
            await self.current_power()
        )
        logger.info("config: " + str(config))

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
