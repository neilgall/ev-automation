import aiohttp
import asyncio
import json
import os
from renault_api.renault_client import RenaultClient
from renault_api.renault_vehicle import RenaultVehicle

async def connect_vehicle(
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
        account.accountId for account in person.accounts
        if account.accountType == "MYRENAULT"
    )
    account = await client.get_api_account(accountId)
    vehicles = await account.get_vehicles()
    vin = next(
        vehicle.vin for vehicle in vehicles.vehicleLinks 
        if vehicle.vehicleDetails.registrationNumber == registration
    )
    return await account.get_api_vehicle(vin)


async def main():
    async with aiohttp.ClientSession() as websession:
        vehicle = await connect_vehicle(
            websession,
            os.getenv("RENAULT_USERNAME"),
            os.getenv("RENAULT_PASSWORD"),
            os.getenv("RENAULT_REGISTRATION")
        )
        print(await vehicle.get_battery_status())

if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
