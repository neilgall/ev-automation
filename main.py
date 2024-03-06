import aiohttp
import argparse
import asyncio
import datetime as dt
import dotenv
import logging
import os
from async_cron.job import CronJob
from async_cron.schedule import Scheduler
from datetime import datetime, time
from devices.andersen import AndersenA2
from devices.vehicle import Vehicle, Credentials
from model.config import Environment, Status, Config, get_config
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


async def configure(env: Environment, max_grid_charge: int):
    async with aiohttp.ClientSession() as session:
        vehicle = await get_vehicle(session)
        battery = await vehicle.get_battery_status()
        status = Status(
            max_grid_charge=max_grid_charge,
            battery_level=battery.batteryLevel,
            now=dt.datetime.now().time()
        )
        config = get_config(env, status)

        andersen = get_andersen_a2()
        andersen.set_max_solar(config.max_solar)


async def update():
    env = Environment(
        cheap_rate_start=dt.time(hour=0, minute=30),
        cheap_rate_end=dt.time(hour=4, minute=25)
    )
    await configure(env, 60)


async def main():
    msh = Scheduler(locale="en_GB")
    msh.add_job(CronJob().every(15).minute.go(update))
    await update()
    await msh.start()


if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("exit")
