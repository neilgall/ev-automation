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
from model.config import Status, Config, get_config
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


async def configure(max_charge: int):
    async with aiohttp.ClientSession() as session:
        vehicle = await get_vehicle(session)
        battery = await vehicle.get_battery_status()
        status = Status(
            max_charge=max_charge,
            battery_level=battery.batteryLevel,
            now=dt.datetime.now().time()
        )
        config = get_config(status)

        andersen = get_andersen_a2()
        andersen.set_max_solar(config.max_solar)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, choices=range(0, 101), default=80)
    args = parser.parse_args()

    asyncio.run(configure(args.limit))
