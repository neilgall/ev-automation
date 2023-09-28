import pytest
from .models import Intent, ChargeState, CurrentPower, Configuration
from .statemachine import StateMachine, ChargeSource

@pytest.fixture
def nothing_charging() -> StateMachine:
    return StateMachine()

@pytest.fixture
def car_charging_from_solar() -> StateMachine:
    return StateMachine(car=ChargeSource.SOLAR)


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

@pytest.fixture
def insufficient_solar_for_car() -> CurrentPower:
    return CurrentPower(
        solar_watts = 1200,
        battery_watts = 0,
        consumption = 500,
        grid_import_watts = 0,
        grid_export_watts = 700,
        grid_offpeak = False
    )


def test_start_car_charging_when_solar_is_sufficient(
    nothing_charging,
    normal_intent,
    half_charged,
    sufficient_solar_for_car
):
    # should remain in house charge state for 5 updates
    for i in range(5):
        config = nothing_charging.update(normal_intent, half_charged, sufficient_solar_for_car)
        assert config == Configuration(
            target_charge_car = normal_intent.target_charge_car,
            target_charge_house = normal_intent.target_charge_house,
            house_charge_enable = True,
            house_charge_max_watts = 2400,
            car_charge_enable = False,
            car_charge_max_solar = 0
        )

    # should enter car charging state on 6th update
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
    # should remain in mixed charge state for 29 updates
    for i in range(29):
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
