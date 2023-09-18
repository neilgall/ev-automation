import andersen_ev

SCHEDULE_SLOT = 4

class AndersenA2:
    def __init__(self, username: str, password: str, device_name: str):
        self._a2 = andersen_ev.AndersenA2()
        self._a2.authenticate(username, password)
        self._device = self._a2.device_by_name(device_name)
        self._deviceId = self._device["id"]

    def get_charge_schedule(self):
        return self._a2.get_schedule(self._deviceId, SCHEDULE_SLOT)


if __name__ == "__main__":
    import dotenv, os
    dotenv.load_dotenv()
    a2 = AndersenA2(
        os.getenv("ANDERSEN_USERNAME"),
        os.getenv("ANDERSEN_PASSWORD"),
        os.getenv("ANDERSEN_DEVICE_NAME")
    )
    print(a2.get_charge_schedule())