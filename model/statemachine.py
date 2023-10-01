from enum import Enum
from .models import Intent, ChargeState, CurrentPower, Configuration


MINIMUM_SOLAR_WATTS_TO_CHARGE_CAR = 1400
MINIMUM_SOLAR_WATTS_TO_CHARGE_HOUSE = 500
MAXIMUM_POLL_INTERVALS_ABOVE_MINIMUM_POWER = 4
MAXIMUM_POLL_INTERVALS_BELOW_MINIMUM_POWER = 10


class ChargeSource(Enum):
    NONE = 0
    SOLAR = 1
    GRID = 2


class Average:
    """
    Stores a history of boolean values and indicates when at least
    half of them are True
    """
    def __init__(self, length: int):
        self._history = []
        self._length = length
        self._threshold = length // 2

    def apply(self, state: bool) -> bool:
        self._history = [*self._history, 1 if state else 0][-self._length:]
        return sum(self._history) > self._threshold


class StateMachine:
    """
    A state machine which consumes ChargeState and CurrentPower events
    and produces a Configuration on each update
    """
    def __init__(self, *, car=ChargeSource.NONE, house=ChargeSource.NONE):
        self._car = car
        self._house = house
        self._sufficient_solar_for_car = Average(MAXIMUM_POLL_INTERVALS_ABOVE_MINIMUM_POWER)
        self._insufficient_solar_for_car = Average(MAXIMUM_POLL_INTERVALS_BELOW_MINIMUM_POWER)

    def update(self, 
        intent: Intent, 
        charge_state: ChargeState,
        current_power: CurrentPower
    ) -> Configuration:
        """
        Given an Intent, a ChargeState and CurrentPower, determine the new Configuration
        """
        excess_power = current_power.solar_watts - current_power.consumption_watts

        if charge_state.current_charge_car >= intent.target_charge_car:
            # Charge car until it reaches the target
            self._car = ChargeSource.NONE
        else:
            match self._car:
                case ChargeSource.SOLAR:
                    # Stop charging if solar level drops below minimum
                    if self._insufficient_solar_for_car.apply(excess_power < MINIMUM_SOLAR_WATTS_TO_CHARGE_CAR):
                        self._car = ChargeSource.NONE

                case ChargeSource.GRID:
                    # Stop charging if offpeak period ends
                    if not current_power.grid_offpeak and not intent.charge_car_regardless:
                        self._car = ChargeSource.NONE

                case ChargeSource.NONE:
                    # Charge from grid off-peak
                    if current_power.grid_offpeak:
                        self._car = ChargeSource.GRID

                    # Start charging from solar if solar level is above minimum
                    elif self._sufficient_solar_for_car.apply(excess_power > MINIMUM_SOLAR_WATTS_TO_CHARGE_CAR):
                        self._car = ChargeSource.SOLAR
            
        if self._car == ChargeSource.SOLAR or charge_state.current_charge_house >= intent.target_charge_house:
            self._house = ChargeSource.NONE
        else:
            match self._house:
                case ChargeSource.SOLAR:
                    pass

                case ChargeSource.GRID:
                    if not current_power.grid_offpeak:
                        self._house = ChargeSource.NONE

                case ChargeSource.NONE:
                    if current_power.grid_offpeak:
                        self._house = ChargeSource.GRID
                    elif current_power.solar_watts > 0:
                        self._house = ChargeSource.SOLAR


        if self._car == ChargeSource.SOLAR and excess_power > MINIMUM_SOLAR_WATTS_TO_CHARGE_CAR:
            car_max_solar = 100
        else:
            car_max_solar = 0
                
        return Configuration(
            target_charge_car = intent.target_charge_car,
            target_charge_house = intent.target_charge_house,
            house_charge_enable = self._house != ChargeSource.NONE,
            house_charge_max_watts = 2400,
            car_charge_enable = self._car != ChargeSource.NONE,
            car_charge_max_solar = car_max_solar
        )
