import aiohttp
import asyncio
import dotenv
import os
from fastapi import FastAPI, Request
from controller.controller import Controller
from model import CurrentPower, ChargeState
from services.andersen import AndersenA2
from services.givenergy import GivEnergy
from services.renault import connect_vehicle

dotenv.load_dotenv()
app = FastAPI()


def require_env(name: str) -> str:
    """
    Read an environment variable, raising an Error if not defined
    """
    value = os.getenv(name)
    if not value:
        raise Exception(f"Required environment variable {name} not defined")
    return value


async def lifespan(app: FastAPI):
    """
    FastAPI lifespan handler
    """
    andersen = AndersenA2(
        require_env("ANDERSEN_USERNAME"),
        require_env("ANDERSEN_PASSWORD"),
        require_env("ANDERSEN_DEVICE_NAME"),
    )
    givenergy = GivEnergy(
        require_env("GIVENERGY_IPADDRESS")
    )
    async with aiohttp.ClientSession() as websession:
        vehicle = await connect_vehicle(
            websession,
            require_env("RENAULT_USERNAME"),
            require_env("RENAULT_PASSWORD"),
            require_env("RENAULT_REGISTRATION"),
        )
        controller = Controller(givenergy=givenergy, andersen=andersen, vehicle=vehicle)
        yield {
            "andersen": andersen,
            "givenergy": givenergy,
            "vehicle": vehicle,
            "controller": controller
        }
        

app = FastAPI(lifespan=lifespan)

@app.get("/charge")
async def get_charge(request: Request) -> ChargeState:
    return await request.state.controller.charge_state()

@app.get("/power")
async def get_power(request: Request) -> CurrentPower:
    return await request.state.controller.current_power()

