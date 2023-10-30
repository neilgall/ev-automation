import andersen_ev
import aiohttp
import asyncio
import dotenv
import logging
import os
from async_cron.job import CronJob
from async_cron.schedule import Scheduler
from dataclasses import dataclass
from datetime import datetime, time
from renault_api.renault_client import RenaultClient
from renault_api.renault_vehicle import RenaultVehicle
from typing import Awaitable, Callable


logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

dotenv.load_dotenv()


def require_env(name: str) -> str:
    """
    Read an environment variable, raising an Error if not defined
    """
    value = os.getenv(name)
    if not value:
        raise Exception(f"Required environment variable {name} not defined")
    return value


@dataclass
class Config:
    charge: bool
    max_solar: int


class AndersenA2:
    def __init__(self, username: str, password: str, device_name: str):
        self._a2 = andersen_ev.AndersenA2()
        self._a2.authenticate(username, password)
        self._device = self._a2.device_by_name(device_name)
        self._deviceId = self._device["id"]

    def configure(self, config: Config):
        logging.info(f"configure {config}")
        if config.charge:
            self._a2.set_solar(self._deviceId, False, False, 100 - config.max_solar)
            self._a2.set_all_schedules_disabled(self._deviceId)
            self._a2.user_unlock(self._deviceId)
        else:
            self._a2.user_lock(self._deviceId)


def get_andersen_a2() -> AndersenA2:
    return AndersenA2(
        require_env("ANDERSEN_USERNAME"),
        require_env("ANDERSEN_PASSWORD"),
        require_env("ANDERSEN_DEVICE_NAME"),
    )

async def renault_vehicle(
    session: aiohttp.ClientSession,
    username: str,
    password: str,
    registration: str
) -> RenaultVehicle:
    client = RenaultClient(websession=session, locale="fr_FR")
    await client.session.login(username, password)
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
        if vehicle.vehicleDetails.registrationNumber == registration
    )
    return await account.get_api_vehicle(vin)


async def get_renault_vehicle(session: aiohttp.ClientSession) -> RenaultVehicle:
    return await renault_vehicle(
        session,
        require_env("RENAULT_USERNAME"),
        require_env("RENAULT_PASSWORD"),
        require_env("RENAULT_REGISTRATION")
    )

class Controller:
    def __init__(self, act: Callable[[Config], Awaitable[None]]):
        self._config = Config(charge=False, max_solar=0)
        self._act = act

    def _next_state(self, now: time) -> Config:
        if time(0, 30) <= now <= time(4, 30):
            return Config(charge=True, max_solar=0)
        else:
            return Config(charge=False, max_solar=0)
        
    async def update(self, now: time):
        config = self._next_state(now)
        if config != self._config:
            self._config = config
            await self._act(config)


async def configure(config: Config):
    if config.charge:
        try:
            async with aiohttp.ClientSession() as session:
                vehicle = await get_renault_vehicle(session)
                battery = await vehicle.get_battery_status()
                if not battery.plugStatus:
                    logger.info("Skipping requested charge as vehicle is unplugged")
                    return
        except Exception as e:
            logger.warn(f"Unable to check vehicle battery status: {e}")

    andersen_a2().configure(config)


async def main():
    controller = Controller(configure)
    logging.info("Controller started")

    async def update():
        await controller.update(datetime.now().time())

    msh = Scheduler(locale="en_GB")
    msh.add_job(CronJob().every(1).minute.go(update))

    await update()
    await msh.start()


if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print('exit')
