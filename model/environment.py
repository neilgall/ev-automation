import datetime as dt
from dataclasses import dataclass


@dataclass
class Environment:
    cheap_rate_start: dt.time
    cheap_rate_end: dt.time
    ready_by: dt.time
    battery_capacity_kwh: float
    charge_rate_kw: float

    @property
    def cheap_rate_duration_minutes(self) -> int:
        now = dt.datetime.now()
        duration = self.next_cheap_rate_end(now) - self.next_cheap_rate_start(now)
        return int(duration.total_seconds() / 60)

    def next_cheap_rate_start(self, now: dt.datetime) -> dt.datetime:
        day_offset = 0 if now.time() < self.cheap_rate_end else 1
        return dt.datetime.combine(
            date=now.date() + dt.timedelta(days=day_offset), time=self.cheap_rate_start
        )

    def next_cheap_rate_end(self, now: dt.datetime) -> dt.datetime:
        day_offset = 0 if now.time() < self.cheap_rate_end else 1
        return dt.datetime.combine(
            date=now.date() + dt.timedelta(days=day_offset), time=self.cheap_rate_end
        )

    def next_ready_by(self, now: dt.datetime) -> dt.datetime:
        day_offset = 0 if now.time() < self.ready_by else 1
        return dt.datetime.combine(
            date=now.date() + dt.timedelta(days=day_offset), time=self.ready_by
        )

    def charge_minutes_needed(
        self, battery_level: int, target_battery_level: int
    ) -> int:
        kwh_needed = (
            (target_battery_level - battery_level) / 100 * self.battery_capacity_kwh
        )
        hours_needed = kwh_needed / self.charge_rate_kw
        return int(hours_needed * 60)
