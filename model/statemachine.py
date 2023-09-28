from enum import Enum
from .models import Intent, ChargeState, CurrentPower, Configuration


MINIMUM_SOLAR_WATTS_TO_CHARGE_CAR = 1400
MINIMUM_SOLAR_WATTS_TO_CHARGE_HOUSE = 500
MAXIMUM_POLL_INTERVALS_ABOVE_MINIMUM_POWER = 6
MAXIMUM_POLL_INTERVALS_BELOW_MINIMUM_POWER = 60


class ChargeSource(Enum):
    NONE = 0
    SOLAR = 1
    GRID = 2


class Hysteresis:
    def __init__(self, limit: int):
        self._count = 0
        self._limit = limit

    def apply(self, state: bool) -> bool:
        if not state:
            self._count = 0
            return False
        if self._count < self._limit:
            self._count += 1
            return self._count == self._limit


class StateMachine:
    """
    A state machine controlling the overall system
    """
    def __init__(self):
        self._car = ChargeSource.NONE
        self._house = ChargeSource.NONE
        self._sufficient_solar_for_car = Hysteresis(MAXIMUM_POLL_INTERVALS_ABOVE_MINIMUM_POWER)
        self._insufficient_solar_for_car = Hysteresis(MAXIMUM_POLL_INTERVALS_BELOW_MINIMUM_POWER)

    def update(self, 
        intent: Intent, 
        charge_state: ChargeState,
        current_power: CurrentPower
    ) -> Configuration:
        """
        Given an Intent, a ChargeState and CurrentPower, determine the new Configuration
        """
        excess_power = current_power.solar_watts - current_power.consumption

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
                    if current_power.solar_watts > 0:
                        self._house = ChargeSource.SOLAR
                    elif current_power.grid_offpeak:
                        self._house = ChargeSource.GRID

        return Configuration(
            target_charge_car = intent.target_charge_car,
            target_charge_house = intent.target_charge_house,
            house_charge_enable = self._house == ChargeSource.SOLAR,
            house_charge_max_watts = 2400,
            car_charge_enable = self._car != ChargeSource.NONE,
            car_charge_max_solar = 100 if self._car == ChargeSource.SOLAR else 0
        )