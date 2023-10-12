import time
from givenergy_modbus.client import GivEnergyClient
from givenergy_modbus.model.inverter import Inverter
from givenergy_modbus.model.plant import Plant
from datetime import datetime, time, timedelta
from time import sleep


def retry_on_keyerror(f):
    def wrapped(self, *args, **kwargs):
        for attempt in range(5):
            try:
                return f(self, *args, **kwargs)
            except KeyError as e:
                error = e
                self._last_refresh = datetime.fromtimestamp(0)
                sleep(1)
        raise error
    return wrapped


class GivEnergy:
    def __init__(self, ip_address: str):
        self._client = GivEnergyClient(ip_address)
        self._last_refresh = datetime.fromtimestamp(0)

    def _refresh(self) -> Plant:
        now = datetime.now()
        if now - self._last_refresh > timedelta(seconds=10):
            plant = Plant(number_batteries=1)
            self._client.refresh_plant(plant, full_refresh=True)
            self._last_refresh = now
            self._plant = plant
        return self._plant

    @retry_on_keyerror
    def current_charge(self) -> int:
        plant = self._refresh()
        return plant.inverter.battery_percent

    @retry_on_keyerror
    def solar_watts(self) -> int:
        plant = self._refresh()
        return plant.inverter.p_pv1 + self._plant.inverter.p_pv2

    @retry_on_keyerror
    def battery_watts(self) -> int:
        plant = self._refresh()
        return plant.inverter.p_battery

    @retry_on_keyerror
    def consumption_watts(self) -> int:
        plant = self._refresh()
        return plant.inverter.p_load_demand

    @retry_on_keyerror
    def grid_import_watts(self) -> int:
        plant = self._refresh()
        return max(0, plant.inverter.p_grid_apparent)

    @retry_on_keyerror
    def grid_export_watts(self) -> int:
        plant = self._refresh()
        return max(0, -plant.inverter.p_grid_apparent)

    @retry_on_keyerror
    def grid_offpeak(self) -> bool:
        plant = self._refresh()
        charge_slot_start, charge_slot_end = plant.inverter.charge_slot_1
        now = datetime.now().time()
        return charge_slot_start < now < charge_slot_end

    def enable_charge(self):
        self._client.enable_charge()

    def disable_charge(self):
        self._client.disable_charge()

    def enable_discharge(self):
        self._client.set_mode_dynamic()

    def disable_discharge(self):
        self._client.disable_discharge()

    def set_charge_target(self, target: int):
        self._client.enable_charge_target(target)

    def set_charge_rate(self, rate: int):
        self._client.set_battery_charge_limit(rate // 52)


if __name__ == "__main__":
    g = GivEnergy("10.180.1.188")
    print("solar_watts=", g.solar_watts())
    print("battery_watts=", g.battery_watts())
    print("grid_import_watts=", g.grid_import_watts())
    print("grid_export_watts=", g.grid_export_watts())
    print("grid_offpeak=", g.grid_offpeak())
