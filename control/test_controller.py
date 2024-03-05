# import pytest
# from datetime import datetime, time, timedelta
# from model import Config, Intent, State
# from typing import List
# from .controller import Controller


# @pytest.fixture
# def config_list() -> List[Config]:
#     return list()


# @pytest.fixture
# def controller(config_list) -> Controller:
#     async def append(item):
#         config_list.append(item)

#     return Controller(append)


# @pytest.mark.asyncio
# async def test_does_not_start_at_0029(controller, config_list):
#     await controller.update(State(plugged_in=True, current_charge=50, now=datetime(2023, 10, 30, 0, 29, 45)))
#     assert config_list == []


# @pytest.mark.asyncio
# async def test_starts_at_0030(controller, config_list):
#     await controller.update(State(plugged_in=True, current_charge=50, now=datetime(2023, 10, 30, 0, 29, 45)))
#     await controller.update(State(plugged_in=True, current_charge=50, now=datetime(2023, 10, 30, 0, 30, 1)))
#     assert len(config_list) == 1
#     assert config_list[-1] == Config(charge=True, max_solar=0)


# @pytest.mark.asyncio
# async def test_does_not_charge_if_unplugged(controller, config_list):
#     await controller.update(State(plugged_in=False, current_charge=50, now=datetime(2023, 10, 30, 0, 30, 59)))
#     assert len(config_list) == 0


# @pytest.mark.asyncio
# async def test_charges_until_0429(controller, config_list):
#     await controller.update(State(plugged_in=True, current_charge=0, now=datetime(2023, 10, 30, 0, 30, 0)))
#     await controller.update(State(plugged_in=True, current_charge=0, now=datetime(2023, 10, 30, 1, 30, 0)))
#     await controller.update(State(plugged_in=True, current_charge=0, now=datetime(2023, 10, 30, 2, 30, 0)))
#     await controller.update(State(plugged_in=True, current_charge=0, now=datetime(2023, 10, 30, 4, 29, 0)))
#     assert len(config_list) == 1
#     assert config_list[-1] == Config(charge=True, max_solar=0)


# @pytest.mark.asyncio
# async def test_stops_when_target_reached(controller, config_list):
#     await controller.update(State(plugged_in=True, current_charge=60, now=datetime(2023, 10, 30, 0, 30, 0)))
#     await controller.update(State(plugged_in=True, current_charge=81, now=datetime(2023, 10, 30, 2, 30, 0)))
#     assert len(config_list) == 2
#     assert config_list[-1] == Config(charge=False, max_solar=0)


# @pytest.mark.asyncio
# async def test_stops_at_0430(controller, config_list):
#     await controller.update(State(plugged_in=True, current_charge=30, now=datetime(2023, 10, 30, 0, 30, 0)))
#     await controller.update(State(plugged_in=True, current_charge=60, now=datetime(2023, 10, 30, 4, 30, 0)))
#     assert config_list[-1] == Config(charge=False, max_solar=0)


# @pytest.mark.asyncio
# @pytest.mark.parametrize("start_charge, start_datetime", [
#     (10, datetime(2023, 10, 29, 21, 31, 0)),
#     (55, datetime(2023, 10, 30, 0, 30, 0))
# ])
# async def test_starts_in_time_to_reach_target(controller, config_list, start_charge, start_datetime):
#     controller.set_intent(Intent(charge_to=95, charge_by=datetime(2023, 10, 30, 5, 0, 0)))
#     await controller.update(State(plugged_in=True, current_charge=start_charge, now=start_datetime - timedelta(minutes=1)))
#     assert len(config_list) == 0
#     await controller.update(State(plugged_in=True, current_charge=start_charge, now=start_datetime))
#     assert len(config_list) == 1
#     assert config_list[-1] == Config(charge=True, max_solar=0)

# @pytest.mark.asyncio
# async def test_stops_if_target_charge_reached_early(controller, config_list):
#     controller.set_intent(Intent(charge_to=95, charge_by=datetime(2023, 10, 30, 6, 0, 0)))
#     await controller.update(State(plugged_in=True, current_charge=40, now=datetime(2023, 10, 30, 0, 30, 0)))
#     await controller.update(State(plugged_in=True, current_charge=60, now=datetime(2023, 10, 30, 2, 30, 0)))
#     await controller.update(State(plugged_in=True, current_charge=80, now=datetime(2023, 10, 30, 4, 30, 0)))
#     assert len(config_list) == 1
#     await controller.update(State(plugged_in=True, current_charge=96, now=datetime(2023, 10, 30, 5, 30, 0)))
#     assert len(config_list) == 2
#     assert config_list[-1] == Config(charge=False, max_solar=0)
