import aiohttp
import asyncio
import dotenv
import os
import time
from async_cron.job import CronJob
from async_cron.schedule import Scheduler
from controller import Controller
from model import Configuration
from services.andersen import AndersenA2
from services.givenergy import GivEnergy
from services.renault import Renault

dotenv.load_dotenv()


def require_env(name: str) -> str:
    """
    Read an environment variable, raising an Error if not defined
    """
    value = os.getenv(name)
    if not value:
        raise Exception(f"Required environment variable {name} not defined")
    return value



async def main():
    andersen = AndersenA2(
        require_env("ANDERSEN_USERNAME"),
        require_env("ANDERSEN_PASSWORD"),
        require_env("ANDERSEN_DEVICE_NAME"),
    )
    controller = Controller(givenergy=None, andersen=andersen, vehicle=None)

    def offpeak():
        controller.apply_configuration(Configuration(
            target_charge_car=80,
            target_charge_house=100,
            house_charge_enable=True,
            house_charge_max_watts=1300,
            car_charge_enable=True,
            car_charge_max_solar=0
        ))

    def morning():
        controller.apply_configuration(Configuration(
            target_charge_car=80,
            target_charge_house=100,
            house_charge_enable=True,
            house_charge_max_watts=2600,
            car_charge_enable=False,
            car_charge_max_solar=0
        ))

    def daytime():
        controller.apply_configuration(Configuration(
            target_charge_car=80,
            target_charge_house=100,
            house_charge_enable=True,
            house_charge_max_watts=2600,
            car_charge_enable=True,
            car_charge_max_solar=100
        ))

    def evening():
        controller.apply_configuration(Configuration(
            target_charge_car=80,
            target_charge_house=100,
            house_charge_enable=True,
            house_charge_max_watts=2600,
            car_charge_enable=False,
            car_charge_max_solar=0
        ))

    dst = time.localtime().tm_isdst
    msh = Scheduler(locale="en_GB")
    msh.add_job(CronJob(name="offpeak").day.at("23:30" if dst else "00:30").go(offpeak))
    msh.add_job(CronJob(name="morning").day.at("03:30" if dst else "04:30").go(morning))
    msh.add_job(CronJob(name="daytime").day.at("10:00" if dst else "11:00").go(daytime))
    msh.add_job(CronJob(name="evening").day.at("15:30" if dst else "16:30").go(evening))
    await msh.start()

try:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
except KeyboardInterrupt:
    print('exit')
