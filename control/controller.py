from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from model import Config, Intent, State
from typing import Awaitable, Callable, Optional, Tuple


BATTERY_CAPACITY_KWH = 60
CHARGE_RATE_KW = 7.3
OFFPEAK_START = time(0, 30)
OFFPEAK_END = time(4, 30)


class Controller:
    def __init__(self, apply: Callable[[Config], Awaitable[None]]):
        self._config = Config(charge=False, max_solar=0)
        self._apply = apply
        self._intent = Intent(charge_to=80, offpeak_only=True)

    def set_intent(self, intent: Intent):
        assert 75 <= intent.charge_to <= 100
        self._intent = intent

    def _next(self, state: State) -> Config:
        if state.plugged_in and self._should_charge(state):
            return Config(charge=True, max_solar=0)
        else:
            return Config(charge=False, max_solar=0)

    def _should_charge(self, state: State) -> bool:
        if self._intent.charge_to < state.current_charge:
            return False
        
        if self._intent.offpeak_only:
            return OFFPEAK_START <= state.now < OFFPEAK_END

        return True

    async def update(self, state: State):
        config = self._next(state)
        if config != self._config:
            self._config = config
            await self._apply(config)


def add_time(t: time, d: timedelta) -> time:
    return (datetime.combine(date(2000, 1, 1), t) + d).time()
