import pytest
from datetime import datetime, time
from model import Config, Intent, State
from typing import List
from .controller import Controller


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
    await controller.update(State(plugged_in=True, current_charge=50, now=time(0, 29)))
    assert config_list == []


@pytest.mark.asyncio
async def test_enables_grid_charging_at_0030(controller, config_list):
    await controller.update(State(plugged_in=True, current_charge=50, now=time(0, 29)))
    await controller.update(State(plugged_in=True, current_charge=50, now=time(0, 30)))
    assert len(config_list) == 1
    assert config_list[-1] == Config(charge=True, max_solar=0)


@pytest.mark.asyncio
async def test_does_not_charge_if_unplugged(controller, config_list):
    await controller.update(State(plugged_in=False, current_charge=50, now=time(0, 30)))
    assert len(config_list) == 0


@pytest.mark.asyncio
async def test_keeps_grid_charging_until_0429(controller, config_list):
    await controller.update(State(plugged_in=True, current_charge=0, now=time(0, 30)))
    await controller.update(State(plugged_in=True, current_charge=0, now=time(1, 30)))
    await controller.update(State(plugged_in=True, current_charge=0, now=time(2, 30)))
    await controller.update(State(plugged_in=True, current_charge=0, now=time(4, 29)))
    assert len(config_list) == 1
    assert config_list[-1] == Config(charge=True, max_solar=0)


@pytest.mark.asyncio
async def test_disables_grid_charging_at_0430(controller, config_list):
    await controller.update(State(plugged_in=True, current_charge=0, now=time(0, 30)))
    await controller.update(State(plugged_in=True, current_charge=0, now=time(4, 30)))
    assert config_list[-1] == Config(charge=False, max_solar=0)


@pytest.mark.asyncio
async def test_does_not_stop_after_offpeak_if_target_not_reached(controller, config_list):
    controller.set_intent(Intent(charge_to=95, charge_by=datetime(2023, 10, 30, 8, 0, 0)))
    await controller.update(State(plugged_in=True, current_charge=60, now=time(0, 30)))
    await controller.update(State(plugged_in=True, current_charge=80, now=time(4, 45)))
    assert len(config_list) == 1
    assert config_list[-1] == Config(charge=True, max_solar=0)


@pytest.mark.asyncio
async def test_stops_when_target_charge_reached(controller, config_list):
    controller.set_intent(Intent(charge_to=95, charge_by=datetime(2023, 10, 30, 6, 0, 0)))
    await controller.update(State(plugged_in=True, current_charge=40, now=time(0, 30)))
    await controller.update(State(plugged_in=True, current_charge=60, now=time(2, 30)))
    await controller.update(State(plugged_in=True, current_charge=80, now=time(4, 30)))
    assert len(config_list) == 1
    await controller.update(State(plugged_in=True, current_charge=96, now=time(5, 30)))
    assert len(config_list) == 2
    assert config_list[-1] == Config(charge=False, max_solar=0)
