import andersen_ev
import logging


class AndersenA2:
    def __init__(self, username: str, password: str, device_name: str):
        self._a2 = andersen_ev.AndersenA2()
        self._a2.authenticate(username, password)
        self._device = self._a2.device_by_name(device_name)
        self._deviceId = self._device["id"]

    def get_solar_override(self):
        solar = self._a2.get_device_solar(self._deviceId)
        return solar.get("getDevice", {}).get("deviceInfo", {}).get("solarOverrideStart", None) is not None

    def set_max_solar(self, max_solar: int):
        logging.info(f"set_max_solar {max_solar}")
        override = self.get_solar_override()
        self._a2.set_solar(self._deviceId, override, False, 100 - max_solar)


if __name__ == "__main__":
    import dotenv, os
    dotenv.load_dotenv()

    a2 = AndersenA2(
        os.getenv("ANDERSEN_USERNAME"),
        os.getenv("ANDERSEN_PASSWORD"),
        os.getenv("ANDERSEN_DEVICE_NAME")
    )
    print(a2.get_solar_override())
