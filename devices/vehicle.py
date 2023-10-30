from aiohttp import ClientSession
from renault_api.renault_client import RenaultClient
from renault_api.renault_vehicle import RenaultVehicle


async def renault_vehicle(
    session: ClientSession, username: str, password: str, registration: str
) -> RenaultVehicle:
    client = RenaultClient(websession=session, locale="fr_FR")
    await client.session.login(username, password)
    person = await client.get_person()
    account_id = next(
        account.accountId
        for account in person.accounts
        if account.accountType == "MYRENAULT"
    )
    account = await client.get_api_account(account_id)
    vehicles = await account.get_vehicles()
    vin = next(
        vehicle.vin
        for vehicle in vehicles.vehicleLinks
        if vehicle.vehicleDetails.registrationNumber == registration
    )
    return await account.get_api_vehicle(vin)
