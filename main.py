import aiohttp
import argparse
import asyncio
import boto3
import datetime as dt
import dotenv
import json
import logging
import os
from async_cron.job import CronJob
from async_cron.schedule import Scheduler
from datetime import datetime, time
from devices.andersen import AndersenA2
from devices.vehicle import Vehicle, Credentials
from iot import IoTClient, IoTThing
from model.config import Environment, Intent, Status, Config, get_config
from typing import Awaitable, Callable


logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

dotenv.load_dotenv()
iot_data = boto3.client("iot-data")


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


def init_iot() -> (IoTClient, IoTThing, IoTThing):
    async def enable_heater(state: bool):
        logging.info(f"set hvac state {state}")
        async with aiohttp.ClientSession() as session:
            vehicle = await get_vehicle(session)
            await vehicle.set_hvac_state(state, 19)

    def heater_state_updated(state: str):
       asyncio.run(enable_heater(state == "on"))

    iot_client = IoTClient()
    heater = iot_client.register_thing(
        thing_name="car_heater",
        property="state",
        default_value="off",
        callback=heater_state_updated
    )
    status = iot_client.register_thing(
        thing_name="car_status",
        property="state",
        default_value={}
    )
    return iot_client, heater, status


async def get_status():
    async with aiohttp.ClientSession() as session:
        vehicle = await get_vehicle(session)
        battery = await vehicle.get_battery_status()
        hvac = await vehicle.get_hvac_state()
        status = Status(
            battery_level=battery.batteryLevel,
            estimated_range=battery.batteryAutonomy,
            hvac_state=hvac,
            now=dt.datetime.now().time()
        )
        logging.info(f"{status}")
        return status


def get_intent():
    data = iot_data.get_thing_shadow(thingName="car_status", shadowName="charge_intent")
    shadow = json.load(data['payload'])
    today = dt.date.today().isoformat()
    max_charge_today = shadow.get("state", {}).get("desired", {}).get(today, "60")
    logging.info(f"maximum requested charge on {today} is {max_charge_today}")
    return Intent(max_grid_charge=int(max_charge_today))


async def main():
    iot_client, iot_heater, iot_status = init_iot()

    def update_iot(status: Status):
        iot_heater.change_shadow_value("on" if status.hvac_state else "off")
        iot_status.change_shadow_value({
            "battery_level": status.battery_level,
            "estimated_range": status.estimated_range
        })
        
    async def update():    
        env = Environment(
            cheap_rate_start=dt.time(hour=0, minute=30),
            cheap_rate_end=dt.time(hour=4, minute=25)
        )
        intent = get_intent()
        status = await get_status()

        config = get_config(env, intent, status)
        andersen = get_andersen_a2()
        andersen.set_charge_from_grid(config.charge_from_grid)
        update_iot(status)

    msh = Scheduler(locale="en_GB")
    msh.add_job(CronJob().every(15).minute.go(update))
    await msh.start()


if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("exit")
