import andersen_ev
import logging


class AndersenA2:
    def __init__(self, username: str, password: str, device_name: str):
        self._a2 = andersen_ev.AndersenA2()
        self._a2.authenticate(username, password)
        self._device = self._a2.device_by_name(device_name)
        self._deviceId = self._device["id"]

    def set_max_solar(self, max_solar: int):
        logging.info(f"set_max_solar {max_solar}")
        self._a2.set_solar(self._deviceId, False, False, 100 - max_solar)
