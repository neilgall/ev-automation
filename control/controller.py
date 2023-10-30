from datetime import datetime, time
from model import Config
from typing import Awaitable, Callable


class Controller:
    def __init__(self, act: Callable[[Config], Awaitable[None]]):
        self._config = Config(charge=False, max_solar=0)
        self._act = act

    def _next_state(self, now: time) -> Config:
        if time(0, 30) <= now <= time(4, 30):
            return Config(charge=True, max_solar=0)
        else:
            return Config(charge=False, max_solar=0)

    async def update(self, now: time):
        config = self._next_state(now)
        if config != self._config:
            self._config = config
            await self._act(config)
