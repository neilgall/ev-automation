import time
from givenergy_modbus.client import GivEnergyClient
from givenergy_modbus.model.inverter import Inverter
from givenergy_modbus.model.plant import Plant
from datetime import datetime, time, timedelta
from time import sleep


def retry_on_keyerror(f):
    def wrapped(*args, **kwargs):
        for attempt in range(5):
            try:
                return f(*args, **kwargs)
            except KeyError as e:
                sleep(1)
                error = e
        raise error
    return wrapped


class GivEnergy:
    def __init__(self, ip_address: str):
        self._client = GivEnergyClient(ip_address)
        self._last_refresh = datetime.fromordinal(1)

    def _refresh(self) -> Plant:
        now = datetime.now()
        if now - self._last_refresh > timedelta(seconds=10):
            self._plant = Plant(number_batteries=1)
            self._client.refresh_plant(self._plant, full_refresh=True)
            self._last_refresh = now

    @retry_on_keyerror
    def current_charge(self) -> int:
        self._refresh()
        return self._plant.inverter.battery_percent


    @retry_on_keyerror
    def solar_watts(self) -> int:
        self._refresh()
        return self._plant.inverter.p_pv1 + self._plant.inverter.p_pv2

    @retry_on_keyerror
    def battery_watts(self) -> int:
        self._refresh()
        return self._plant.inverter.p_battery

    @retry_on_keyerror
    def consumption_watts(self) -> int:
        self._refresh()
        return self._plant.inverter.p_load_demand

    @retry_on_keyerror
    def grid_import_watts(self) -> int:
        self._refresh()
        return max(0, self._plant.inverter.p_grid_apparent)

    @retry_on_keyerror
    def grid_export_watts(self) -> int:
        self._refresh()
        return max(0, -self._plant.inverter.p_grid_apparent)

    @retry_on_keyerror
    def grid_offpeak(self) -> bool:
        self._refresh()
        charge_slot_start, charge_slot_end = self._plant.inverter.charge_slot_1
        now = datetime.now().time()
        return charge_slot_start < now < charge_slot_end


if __name__ == "__main__":
    g = GivEnergy("10.180.1.188")
    print("solar_watts=", g.solar_watts())
    print("battery_watts=", g.battery_watts())
    print("grid_import_watts=", g.grid_import_watts())
    print("grid_export_watts=", g.grid_export_watts())
    print("grid_offpeak=", g.grid_offpeak())
