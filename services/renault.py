import aiohttp
import asyncio
import json
import os
import time
from functools import wraps
from renault_api.renault_client import RenaultClient
from renault_api.renault_vehicle import RenaultVehicle
from renault_api.kamereon.models import KamereonVehicleBatteryStatusData


def ttl_cache(seconds: int):
    def decorator(func):
        state = { "value": None, "expiry": None }
        @wraps(func)
        async def wrapped(*args, **kwargs):
            if state["value"] is None or time.time() > state["expiry"]:
                state["value"] = await func(*args, **kwargs)
                state["expiry"] = time.time() + seconds
            return state["value"]
        return wrapped
    return decorator


class Renault:
    def __init__(self, vehicle: RenaultVehicle):
        self._vehicle = vehicle

    @classmethod
    async def connect(
        cls: "Renault",
        websession: aiohttp.ClientSession,
        username: str,
        password: str,
        registration: str
    ) -> RenaultVehicle:
        """
        Connect and authenticate to the Renault API and obtain the RenaultVehicle
        instance for the given registration.
        """
        client = RenaultClient(websession=websession, locale="en_GB")
        await client.session.login(username, password)
        person = await client.get_person()
        accountId = next(
            account.accountId
            for account in person.accounts
            if account.accountType == "MYRENAULT"
        )
        account = await client.get_api_account(accountId)
        vehicles = await account.get_vehicles()
        vin = next(
            vehicle.vin
            for vehicle in vehicles.vehicleLinks
            if vehicle.vehicleDetails.registrationNumber == registration
        )
        return Renault(await account.get_api_vehicle(vin))

    @ttl_cache(seconds=900)
    async def get_battery_status(self) -> KamereonVehicleBatteryStatusData:
        return await self._vehicle.get_battery_status()


async def main():
    async with aiohttp.ClientSession() as websession:
        vehicle = await Renault.connect(
            websession,
            os.getenv("RENAULT_USERNAME"),
            os.getenv("RENAULT_PASSWORD"),
            os.getenv("RENAULT_REGISTRATION"),
        )
        print(await vehicle.get_battery_status())
        print(await vehicle.get_battery_status())


if __name__ == "__main__":
    import dotenv

    dotenv.load_dotenv()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
