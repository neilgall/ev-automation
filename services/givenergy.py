import time
from givenergy_modbus.client import GivEnergyClient
from givenergy_modbus.client.commands import (
    set_enable_charge,
    set_enable_discharge,
    set_charge_target,
    set_charge_rate
)
from givenergy_modbus.model.inverter import Inverter
from givenergy_modbus.model.plant import Plant
from datetime import datetime, time, timedelta
from time import sleep


def retry_on_keyerror(f):
    def wrapped(self, *args, **kwargs):
        for attempt in range(5):
            try:
                return f(*args, **kwargs)
            except KeyError as e:
                error = e
                self._last_refresh = datetime.fromordinal(1)
                time.sleep(1)
        raise error
    return wrapped


class GivEnergy:
    def __init__(self, ip_address: str):
        self._client = GivEnergyClient(ip_address)
        self._plant = Plant(number_batteries=1)
        self._last_refresh = datetime.fromordinal(1)

    async def _refresh(self) -> Plant:
        now = datetime.now()
        if now - self._last_refresh > timedelta(seconds=10):
            await self._client.refresh_plant(self._plant, full_refresh=True)
            self._last_refresh = now

    @retry_on_keyerror
    async def current_charge(self) -> int:
        await self._refresh()
        return self._plant.inverter.battery_percent

    @retry_on_keyerror
    async def solar_watts(self) -> int:
        await self._refresh()
        return self._plant.inverter.p_pv1 + self._plant.inverter.p_pv2

    @retry_on_keyerror
    async def battery_watts(self) -> int:
        await self._refresh()
        return self._plant.inverter.p_battery

    @retry_on_keyerror
    async def consumption_watts(self) -> int:
        await self._refresh()
        return self._plant.inverter.p_load_demand

    @retry_on_keyerror
    async def grid_import_watts(self) -> int:
        await self._refresh()
        return max(0, self._plant.inverter.p_grid_apparent)

    @retry_on_keyerror
    async def grid_export_watts(self) -> int:
        await self._refresh()
        return max(0, -self._plant.inverter.p_grid_apparent)

    @retry_on_keyerror
    async def grid_offpeak(self) -> bool:
        await self._refresh()
        charge_slot_start, charge_slot_end = self._plant.inverter.charge_slot_1
        now = datetime.now().time()
        return charge_slot_start < now < charge_slot_end

    async def enable_charge(self):
        await self._client.one_shot_command(set_enable_charge(True))

    async def disable_charge(self):
        await self._client.one_shot_command(set_enable_charge(False))

    async def enable_discharge(self):
        await self._client.one_shot_command(set_enable_discharge(True))

    async def disable_discharge(self):
        await self._client.one_shot_command(set_enable_discharge(False))

    async def set_charge_target(self, target: int):
        await self._client.one_shot_command(set_charge_target(target))

    async def set_charge_rate(self, rate: int):
        await self._client.one_shot_command(set_charge_rate(rate))


if __name__ == "__main__":
    g = GivEnergy("10.180.1.188")
    print("solar_watts=", g.solar_watts())
    print("battery_watts=", g.battery_watts())
    print("grid_import_watts=", g.grid_import_watts())
    print("grid_export_watts=", g.grid_export_watts())
    print("grid_offpeak=", g.grid_offpeak())
