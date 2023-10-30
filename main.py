import aiohttp
import asyncio
import dotenv
import logging
import os
from async_cron.job import CronJob
from async_cron.schedule import Scheduler
from control.controller import Controller
from datetime import datetime, time
from devices.andersen import AndersenA2
from devices.vehicle import Vehicle, Credentials
from model import Config, State
from typing import Awaitable, Callable


logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

dotenv.load_dotenv()


def require_env(name: str) -> str:
    """
    Read an environment variable, raising an Error if not defined
    """
    value = os.getenv(name)
    if not value:
        raise Exception(f"Required environment variable {name} not defined")
    return value


def get_andersen_a2() -> AndersenA2:
    return AndersenA2(
        require_env("ANDERSEN_USERNAME"),
        require_env("ANDERSEN_PASSWORD"),
        require_env("ANDERSEN_DEVICE_NAME"),
    )


async def get_vehicle(session: aiohttp.ClientSession) -> Vehicle:
    vehicle = Vehicle(
        session,
        Credentials(
            username=require_env("RENAULT_USERNAME"),
            password=require_env("RENAULT_PASSWORD"),
            registration=require_env("RENAULT_REGISTRATION"),
        ),
    )
    await vehicle.connect()
    return vehicle


async def main():
    async with aiohttp.ClientSession() as session:
        vehicle = await get_vehicle(session)

        async def configure(config: Config):
            get_andersen_a2().configure(config)

        controller = Controller(configure)
        logging.info("Controller started")

        async def update():
            battery = await vehicle.get_battery_status()
            state = State(
                plugged_in=bool(battery.plugStatus),
                current_charge=battery.batteryLevel,
                now=datetime.now()
            )
            await controller.update(state)

        msh = Scheduler(locale="en_GB")
        msh.add_job(CronJob().every(1).minute.go(update))

        await update()
        await msh.start()


if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("exit")
