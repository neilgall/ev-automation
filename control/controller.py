from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from model import Config, Intent, State
from typing import Awaitable, Callable, Optional, Tuple


BATTERY_CAPACITY_KWH = 60
CHARGE_RATE_KW = 7.3


@dataclass
class Action:
    start_at: Optional[time] = time(0, 30)
    stop_at: Optional[time] = time(4, 30)


class Controller:
    def __init__(self, apply: Callable[[Config], Awaitable[None]]):
        self._config = Config(charge=False, max_solar=0)
        self._action = Action(stop_at=None)
        self._apply = apply
        self._intent = Intent(charge_to=80, offpeak_only=True)

    def set_intent(self, intent: Intent):
        assert 75 <= intent.charge_to <= 100
        self._intent = intent

    def _next(self, state: State) -> Tuple[Config, Action]:
        print(f"state: {state}, action: {self._action}")

        if self._action.start_at is not None and self._action.start_at <= state.now:
            return self._start_charge(state)

        if self._action.stop_at is not None and self._action.stop_at <= state.now:
            return self._stop_charge(state)

        if state.current_charge > self._intent.charge_to:
            return self._stop_charge(state)

        return self._config, self._action

    def _start_charge(self, state: State) -> Tuple[Config, Action]:
        if self._intent.offpeak_only:
            action = Action(start_at=None)
        else:
            required_charge_percent = self._intent.charge_to - state.current_charge
            required_charge_kw = BATTERY_CAPACITY_KWH * required_charge_percent / 100
            charge_minutes = int(required_charge_kw / CHARGE_RATE_KW * 60)
            stop_time = add_time(state.now, timedelta(minutes=charge_minutes))
            action = Action(start_at=None, stop_at=stop_time)
        return Config(charge=True, max_solar=0), action

    def _stop_charge(self, state: State) -> Tuple[Config, Action]:
        return Config(charge=False, max_solar=0), Action(stop_at=None)

    async def update(self, state: State):
        config, action = self._next(state)
        if config != self._config:
            self._config = config
            self._action = action
            await self._apply(config)


def add_time(t: time, d: timedelta) -> time:
    return (datetime.combine(date.today(), t) + d).time()
