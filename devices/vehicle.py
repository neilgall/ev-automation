from aiohttp import ClientSession
from dataclasses import dataclass
from datetime import datetime, timedelta
from renault_api.renault_client import RenaultClient
from renault_api.renault_vehicle import RenaultVehicle
from renault_api.kamereon.models import ChargeSchedule, ChargeDaySchedule
import logging


@dataclass
class Credentials:
    username: str
    password: str
    registration: str


class Vehicle:
    def __init__(self, session: ClientSession, credentials: Credentials):
        self._session = session
        self._credentials = credentials
        self._battery = (datetime.fromordinal(1), None)

    async def connect(self):
        client = RenaultClient(websession=self._session, locale="fr_FR")
        await client.session.login(
            self._credentials.username, self._credentials.password
        )
        person = await client.get_person()
        account_id = next(
            account.accountId
            for account in person.accounts
            if account.accountType == "MYRENAULT"
        )
        account = await client.get_api_account(account_id)
        vehicles = await account.get_vehicles()
        vin = next(
            vehicle.vin
            for vehicle in vehicles.vehicleLinks
            if vehicle.vehicleDetails.registrationNumber
            == self._credentials.registration
        )
        self._vehicle = await account.get_api_vehicle(vin)

    async def get_battery_status(self):
        now = datetime.now()
        if self._battery[0] + timedelta(minutes=15) < now:
            self._battery = (now, await self._vehicle.get_battery_status())
            logging.debug(f"battery: {self._battery[1]}")
        return self._battery[1]

    async def get_hvac_state(self) -> bool:
        hvac = await self._vehicle.get_hvac_status()
        return hvac == "on"

    async def set_hvac_state(self, state: bool, temperature: int):
        if state:
            await self._vehicle.set_ac_start(temperature=temperature)
        else:
            await self._vehicle.set_ac_stop()

    async def enable_charge_schedule(self, enable: bool):
        logging.debug(f"enable_charge_schedule {enable}")
        await self._vehicle.set_charge_mode(
            "schedule_mode" if enable else "always_charging"
        )

    async def set_charge_schedule(self, start: str, duration: int):
        logging.debug(f"set_charge_schedule {start},{duration}")
        day_schedule = ChargeDaySchedule(
            startTime=start, duration=duration, raw_data={}
        )
        schedule = ChargeSchedule(
            id=None,
            activated=True,
            monday=day_schedule,
            tuesday=day_schedule,
            wednesday=day_schedule,
            thursday=day_schedule,
            friday=day_schedule,
            saturday=day_schedule,
            sunday=day_schedule,
            raw_data={},
        )
        await self._vehicle.set_charge_schedules([schedule])


if __name__ == "__main__":
    import aiohttp, asyncio, dotenv, os

    async def test():
        async with aiohttp.ClientSession() as session:
            vehicle = Vehicle(
                session,
                Credentials(
                    username=os.environ["RENAULT_USERNAME"],
                    password=os.environ["RENAULT_PASSWORD"],
                    registration=os.environ["RENAULT_REGISTRATION"],
                ),
            )
            await vehicle.connect()
            print(await vehicle.get_battery_status())

    dotenv.load_dotenv()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test())
