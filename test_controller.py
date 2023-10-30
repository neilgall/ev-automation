import pytest
from main import Config, Controller
from datetime import time
from typing import List


@pytest.fixture
def config_list() -> List[Config]:
    return list()

@pytest.fixture
def controller(config_list) -> Controller:
    async def append(item):
        config_list.append(item)
    return Controller(append)

@pytest.mark.asyncio
async def test_disables_grid_charging_at_0029(controller, config_list):
    await controller.update(time(0, 29))
    assert config_list == []

@pytest.mark.asyncio
async def test_enables_grid_charging_at_0030(controller, config_list):
    await controller.update(time(0, 29))
    await controller.update(time(0, 30))
    assert len(config_list) == 1
    assert config_list[-1] == Config(charge=True, max_solar=0)

@pytest.mark.asyncio
async def test_keeps_grid_charging_until_0430(controller, config_list):
    await controller.update(time(0, 30))
    await controller.update(time(1, 30))
    await controller.update(time(2, 30))
    await controller.update(time(4, 30))
    assert len(config_list) == 1
    assert config_list[-1] == Config(charge=True, max_solar=0)

@pytest.mark.asyncio
async def test_disables_grid_charging_at_0431(controller, config_list):
    await controller.update(time(0, 30))
    await controller.update(time(4, 31))
    assert config_list[-1] == Config(charge=False, max_solar=0)
