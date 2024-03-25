import andersen_ev
import datetime as dt
import logging


class AndersenA2:
    def __init__(self, username: str, password: str, device_name: str):
        self._a2 = andersen_ev.AndersenA2()
        self._a2.authenticate(username, password)
        self._device = self._a2.device_by_name(device_name)
        self._deviceId = self._device["id"]

    def get_solar_override(self) -> bool:
        try:
            solar = self._a2.get_device_solar(self._deviceId)
            start_str = solar.get("getDevice", {}).get("deviceInfo", {}).get("solarOverrideStart", None)
            if not start_str:
                return False
            start = dt.datetime.fromisoformat(start_str).replace(tzinfo=None)
            return dt.datetime.utcnow() - start < dt.timedelta(hours=2)
        except Exception as e:
            logging.error(f"failed to fetch solar override: {e}")
            return False

    def set_charge_from_grid(self, charge_from_grid: bool):
        override = self.get_solar_override()
        try:
            logging.info(f"set_charge_from_grid {charge_from_grid} override={override}")
            self._a2.set_solar(
                deviceId=self._deviceId,
                override=override,
                chargeAlways=charge_from_grid,
                maxGridChargePercent=100 if charge_from_grid else 0
            )
        except Exception as e:
            logging.error(f"failed to set charge mode: {e}")


if __name__ == "__main__":
    import dotenv, os
    dotenv.load_dotenv()

    a2 = AndersenA2(
        os.getenv("ANDERSEN_USERNAME"),
        os.getenv("ANDERSEN_PASSWORD"),
        os.getenv("ANDERSEN_DEVICE_NAME")
    )
    print(a2.get_solar_override())
