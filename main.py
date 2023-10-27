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
from typing import Callable

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


class Controller:
    def __init__(self, act: Callable[[Config], None]):
        self._config = Config(charge=False, max_solar=0)
        self._act = act

    def _next_state(self, now: time) -> Config:
        if time(0, 30) <= now <= time(4, 30):
            return Config(charge=True, max_solar=0)
        else:
            return Config(charge=False, max_solar=0)
        
    def update(self, now: time):
        config = self._next_state(now)
        if config != self._config:
            self._config = config
            self._act(config)


async def main():
    def configure(config: Config):
        andersen = AndersenA2(
            require_env("ANDERSEN_USERNAME"),
            require_env("ANDERSEN_PASSWORD"),
            require_env("ANDERSEN_DEVICE_NAME"),
        )
        andersen.configure(config)

    controller = Controller(configure)
    controller.update(datetime.now().time())
    logging.info("Controller started")

    def update():
        controller.update(datetime.now().time())
        
    msh = Scheduler(locale="en_GB")
    msh.add_job(CronJob().every(30).minute.go(update))
    await msh.start()


if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print('exit')
