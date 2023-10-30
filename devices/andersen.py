import andersen_ev
import logging
from dataclasses import dataclass
from model import Config


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
