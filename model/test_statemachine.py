import pytest
from .models import Intent, ChargeState, CurrentPower, Configuration
from .statemachine import (
    StateMachine,
    ChargeSource,
    MAXIMUM_POLL_INTERVALS_ABOVE_MINIMUM_POWER,
    MAXIMUM_POLL_INTERVALS_BELOW_MINIMUM_POWER
)

@pytest.fixture
def nothing_charging() -> StateMachine:
    return StateMachine()

@pytest.fixture
def car_charging_from_solar() -> StateMachine:
    return StateMachine(car=ChargeSource.SOLAR)

@pytest.fixture
def charging_from_grid() -> StateMachine:
    return StateMachine(car=ChargeSource.GRID, house=ChargeSource.GRID)


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
def fully_charged() -> ChargeState:
    return ChargeState(
        current_charge_car = 80,
        current_charge_house = 100
    )

@pytest.fixture
def sufficient_solar_for_car() -> CurrentPower:
    return CurrentPower(
        solar_watts = 2500,
        battery_watts = 0,
        consumption_watts = 500,
        grid_import_watts = 0,
        grid_export_watts = 2000,
        grid_offpeak = False
    )

@pytest.fixture
def insufficient_solar_for_car() -> CurrentPower:
    return CurrentPower(
        solar_watts = 1200,
        battery_watts = 0,
        consumption_watts = 500,
        grid_import_watts = 0,
        grid_export_watts = 700,
        grid_offpeak = False
    )

@pytest.fixture
def offpeak() -> CurrentPower:
    return CurrentPower(
        solar_watts = 0,
        battery_watts = 0,
        consumption_watts = 400,
        grid_import_watts = 400,
        grid_export_watts = 0,
        grid_offpeak = True
    )


def test_start_car_charging_when_solar_is_sufficient(
    nothing_charging,
    normal_intent,
    half_charged,
    sufficient_solar_for_car
):
    # should remain in house charge state for several updates
    for i in range(MAXIMUM_POLL_INTERVALS_ABOVE_MINIMUM_POWER // 2):
        config = nothing_charging.update(normal_intent, half_charged, sufficient_solar_for_car)
        assert config == Configuration(
            target_charge_car = normal_intent.target_charge_car,
            target_charge_house = normal_intent.target_charge_house,
            house_charge_enable = True,
            house_charge_max_watts = 2400,
            car_charge_enable = False,
            car_charge_max_solar = 0
        )

    # should enter car charging state on next update
    config = nothing_charging.update(normal_intent, half_charged, sufficient_solar_for_car)
    assert config == Configuration(
        target_charge_car = normal_intent.target_charge_car,
        target_charge_house = normal_intent.target_charge_house,
        house_charge_enable = False,
        house_charge_max_watts = 2400,
        car_charge_enable = True,
        car_charge_max_solar = 100
    )


def test_stop_car_charging_when_solar_is_insufficient(
    car_charging_from_solar,
    normal_intent,
    half_charged,
    insufficient_solar_for_car
):
    # should remain in mixed charge state for several updates
    for i in range(MAXIMUM_POLL_INTERVALS_BELOW_MINIMUM_POWER // 2):
        config = car_charging_from_solar.update(normal_intent, half_charged, insufficient_solar_for_car)
        assert config == Configuration(
            target_charge_car = normal_intent.target_charge_car,
            target_charge_house = normal_intent.target_charge_house,
            house_charge_enable = False,
            house_charge_max_watts = 2400,
            car_charge_enable = True,
            car_charge_max_solar = 0
        )

    # car will stop charging on next update
    config = car_charging_from_solar.update(normal_intent, half_charged, insufficient_solar_for_car)
    assert config == Configuration(
        target_charge_car = normal_intent.target_charge_car,
        target_charge_house = normal_intent.target_charge_house,
        house_charge_enable = True,
        house_charge_max_watts = 2400,
        car_charge_enable = False,
        car_charge_max_solar = 0
    )

def test_stop_charging_when_target_reached(
    car_charging_from_solar,
    normal_intent,
    fully_charged,
    sufficient_solar_for_car
):
    config = car_charging_from_solar.update(normal_intent, fully_charged, sufficient_solar_for_car)
    assert config == Configuration(
        target_charge_car = normal_intent.target_charge_car,
        target_charge_house = normal_intent.target_charge_house,
        house_charge_enable = False,
        house_charge_max_watts = 2400,
        car_charge_enable = False,
        car_charge_max_solar = 0
    )


def test_start_charging_offpeak(
    nothing_charging,
    normal_intent,
    half_charged,
    offpeak
):
    config = nothing_charging.update(normal_intent, half_charged, offpeak)
    assert config == Configuration(
        target_charge_car = normal_intent.target_charge_car,
        target_charge_house = normal_intent.target_charge_house,
        house_charge_enable = True,
        house_charge_max_watts = 2400,
        car_charge_enable = True,
        car_charge_max_solar = 0
    )

def test_stop_charging_after_offpeak(
    charging_from_grid,
    normal_intent,
    half_charged,
    insufficient_solar_for_car
):
    config = charging_from_grid.update(normal_intent, half_charged, insufficient_solar_for_car)
    assert config == Configuration(
        target_charge_car = normal_intent.target_charge_car,
        target_charge_house = normal_intent.target_charge_house,
        house_charge_enable = False,
        house_charge_max_watts = 2400,
        car_charge_enable = False,
        car_charge_max_solar = 0
    )
