import pytest
from datetime import time
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
    await controller.update(State(current_charge=50, now=time(0, 29)))
    assert config_list == []


@pytest.mark.asyncio
async def test_enables_grid_charging_at_0030(controller, config_list):
    await controller.update(State(current_charge=50, now=time(0, 29)))
    await controller.update(State(current_charge=50, now=time(0, 30)))
    assert len(config_list) == 1
    assert config_list[-1] == Config(charge=True, max_solar=0)


@pytest.mark.asyncio
async def test_keeps_grid_charging_until_0429(controller, config_list):
    await controller.update(State(current_charge=0, now=time(0, 30)))
    await controller.update(State(current_charge=0, now=time(1, 30)))
    await controller.update(State(current_charge=0, now=time(2, 30)))
    await controller.update(State(current_charge=0, now=time(4, 29)))
    assert len(config_list) == 1
    assert config_list[-1] == Config(charge=True, max_solar=0)


@pytest.mark.asyncio
async def test_disables_grid_charging_at_0430(controller, config_list):
    await controller.update(State(current_charge=0, now=time(0, 30)))
    await controller.update(State(current_charge=0, now=time(4, 30)))
    assert config_list[-1] == Config(charge=False, max_solar=0)


@pytest.mark.asyncio
async def test_calculates_stop_time_based_on_starting_charge(controller, config_list):
    controller.set_intent(Intent(charge_to=80, offpeak_only=False))
    await controller.update(State(current_charge=60, now=time(0, 30)))
    await controller.update(State(current_charge=60, now=time(2, 7)))
    assert len(config_list) == 1
    assert config_list[-1] == Config(charge=True, max_solar=0)


@pytest.mark.asyncio
@pytest.mark.parametrize("charge_to, stop_time", [(80, time(2, 8)), (100, time(3, 47))])
async def test_stops_at_calculated_stop_time(
    controller, config_list, charge_to, stop_time
):
    controller.set_intent(Intent(charge_to=charge_to, offpeak_only=False))
    await controller.update(State(current_charge=60, now=time(0, 30)))
    await controller.update(State(current_charge=60, now=stop_time))
    assert len(config_list) == 2
    assert config_list[-1] == Config(charge=False, max_solar=0)


@pytest.mark.asyncio
async def test_stops_charging_if_target_reached_early(controller, config_list):
    controller.set_intent(Intent(charge_to=80, offpeak_only=False))
    await controller.update(State(current_charge=60, now=time(0, 30)))
    await controller.update(State(current_charge=81, now=time(2, 0)))
    assert config_list[-1] == Config(charge=False, max_solar=0)
