import aiohttp
import asyncio
import dotenv
import os
from fastapi import FastAPI, Request
from services.renault import connect_vehicle
from services.andersen import AndersenA2

dotenv.load_dotenv()
app = FastAPI()


def require_env(name: str) -> str:
    """
    Read an environment variable, raising an Error if not defined
    """
    value = os.getenv(name)
    if not value:
        raise Error(f"Required environment variable {name} not defined")
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
    async with aiohttp.ClientSession() as websession:
        vehicle = await connect_vehicle(
            websession,
            require_env("RENAULT_USERNAME"),
            require_env("RENAULT_PASSWORD"),
            require_env("RENAULT_REGISTRATION"),
        )
        yield {
            "andersen": andersen,
            "vehicle": vehicle
        }
        

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def hello(request: Request) -> dict:
    data = await request.state.vehicle.get_battery_status()
    return data.raw_data


