import pytest
from .models import Intent, ChargeState, CurrentPower, Configuration
from .statemachine import StateMachine

@pytest.fixture
def state_machine() -> StateMachine:
    return StateMachine()


@pytest.fixture
def normal_intent() -> Intent:
    return Intent(
        target_charge_car = 80,
        target_charge_house = 100,
        charge_car_regardless = False
    )

@pytest.fixture
def half_charged() -> ChargeState:
    return ChargeState(
        current_charge_car = 50,
        current_charge_house = 50
    )

@pytest.fixture
def sufficient_solar_for_car() -> CurrentPower:
    return CurrentPower(
        solar_watts = 2500,
        battery_watts = 0,
        consumption = 500,
        grid_import_watts = 0,
        grid_export_watts = 2000,
        grid_offpeak = False
    )

def test_sufficient_solar_for_car_charging(
    state_machine,
    normal_intent,
    half_charged,
    sufficient_solar_for_car
):
    # should remain in house charge state for 5 updates
    for i in range(5):
        config = state_machine.update(normal_intent, half_charged, sufficient_solar_for_car)
        assert config == Configuration(
            target_charge_car = normal_intent.target_charge_car,
            target_charge_house = normal_intent.target_charge_house,
            house_charge_enable = True,
            house_charge_max_watts = 2400,
            car_charge_enable = False,
            car_charge_max_solar = 0
        )

    # should enter car charging state on 6th update
    config = state_machine.update(normal_intent, half_charged, sufficient_solar_for_car)
    assert config == Configuration(
        target_charge_car = normal_intent.target_charge_car,
        target_charge_house = normal_intent.target_charge_house,
        house_charge_enable = False,
        house_charge_max_watts = 2400,
        car_charge_enable = True,
        car_charge_max_solar = 100
    )
