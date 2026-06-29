"""Immutable data models for KD Brain.

Money is represented with :class:`~decimal.Decimal` to avoid floating-point
rounding errors in tariff arithmetic. Times are timezone-aware and stored in
UTC internally; conversion to local time happens only at display boundaries.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta, tzinfo
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class PricePoint:
    """A single price interval.

    ``market`` is the raw day-ahead market price (€/kWh, excl. taxes). ``all_in``
    is the consumption price a household actually pays (incl. energy tax, supplier
    markup and VAT). ``feed_in`` is the price received for exported energy.
    """

    start: datetime
    end: datetime
    market: Decimal
    all_in: Decimal
    feed_in: Decimal

    def contains(self, moment: datetime) -> bool:
        """Return whether ``moment`` falls within this interval."""
        return self.start <= moment < self.end


@dataclass(frozen=True, slots=True)
class PriceSeries:
    """An ordered, contiguous collection of :class:`PricePoint` values."""

    points: tuple[PricePoint, ...]
    resolution: timedelta

    @property
    def is_empty(self) -> bool:
        """Return whether the series has no points."""
        return not self.points

    def point_at(self, moment: datetime) -> PricePoint | None:
        """Return the price point active at ``moment``, if any."""
        for point in self.points:
            if point.contains(moment):
                return point
        return None

    def next_point(self, moment: datetime) -> PricePoint | None:
        """Return the first price point that starts at or after ``moment``."""
        for point in self.points:
            if point.start > moment:
                return point
        return None

    def slice_local_day(self, day: date, tz: tzinfo) -> PriceSeries:
        """Return a new series containing only points on the given local day."""
        selected = tuple(
            point for point in self.points if point.start.astimezone(tz).date() == day
        )
        return PriceSeries(points=selected, resolution=self.resolution)

    def min_point(self) -> PricePoint | None:
        """Return the point with the lowest all-in price."""
        if self.is_empty:
            return None
        return min(self.points, key=lambda point: point.all_in)

    def max_point(self) -> PricePoint | None:
        """Return the point with the highest all-in price."""
        if self.is_empty:
            return None
        return max(self.points, key=lambda point: point.all_in)

    def average_all_in(self) -> Decimal | None:
        """Return the mean all-in price across the series, if non-empty."""
        if self.is_empty:
            return None
        total = sum((point.all_in for point in self.points), Decimal(0))
        return total / Decimal(len(self.points))

    def to_hourly(self) -> PriceSeries:
        """Aggregate to hourly resolution by averaging the sub-hour points.

        epexprijzen.nl publishes 15-minute (MTU) data; hourly prices are the
        arithmetic mean of the four quarters, matching the source website.
        """
        if self.resolution >= timedelta(hours=1):
            return self

        buckets: dict[datetime, list[PricePoint]] = defaultdict(list)
        for point in self.points:
            hour_start = point.start.replace(minute=0, second=0, microsecond=0)
            buckets[hour_start].append(point)

        hourly: list[PricePoint] = []
        for hour_start in sorted(buckets):
            group = buckets[hour_start]
            count = Decimal(len(group))
            hourly.append(
                PricePoint(
                    start=hour_start,
                    end=hour_start + timedelta(hours=1),
                    market=sum((p.market for p in group), Decimal(0)) / count,
                    all_in=sum((p.all_in for p in group), Decimal(0)) / count,
                    feed_in=sum((p.feed_in for p in group), Decimal(0)) / count,
                )
            )
        return PriceSeries(points=tuple(hourly), resolution=timedelta(hours=1))

    def as_dicts(self) -> list[dict[str, str | float]]:
        """Serialise points for entity attributes (JSON/Recorder friendly)."""
        return [
            {
                "start": point.start.isoformat(),
                "end": point.end.isoformat(),
                "market": float(point.market),
                "all_in": float(point.all_in),
                "feed_in": float(point.feed_in),
            }
            for point in self.points
        ]


# ---------------------------------------------------------------------------
# Telemetry (M2)
#
# Sign conventions (consistent across the whole integration):
#   - grid power:    + = importing from the grid, - = exporting to the grid
#   - pv power:      >= 0 (production)
#   - battery power: + = charging, - = discharging
#   - load power:    >= 0 (household consumption)
# All powers are in watts (W). Any value may be ``None`` when the corresponding
# entity is not configured or currently unavailable.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class GridState:
    """Grid connection telemetry."""

    power_w: float | None = None  # + import, - export


@dataclass(frozen=True, slots=True)
class PvState:
    """Solar production telemetry."""

    power_w: float | None = None


@dataclass(frozen=True, slots=True)
class BatteryState:
    """Telemetry for a single home battery."""

    soc: float | None = None  # state of charge, percent (0-100)
    power_w: float | None = None  # + charging, - discharging
    capacity_wh: int | None = None
    temp_c: float | None = None


@dataclass(frozen=True, slots=True)
class LoadState:
    """Household load telemetry."""

    power_w: float | None = None
    derived: bool = False  # True when computed instead of measured


@dataclass(frozen=True, slots=True)
class Telemetry:
    """A snapshot of all live device telemetry KD Brain can read."""

    grid: GridState = GridState()
    pv: PvState = PvState()
    batteries: tuple[BatteryState, ...] = ()
    load: LoadState = LoadState()
    imbalance_price: float | None = None  # current imbalance price, €/kWh

    def battery_soc_average(self) -> float | None:
        """Return the mean state of charge across batteries, if known."""
        values = [b.soc for b in self.batteries if b.soc is not None]
        return sum(values) / len(values) if values else None

    def battery_power_total(self) -> float | None:
        """Return the summed battery power across batteries, if known."""
        values = [b.power_w for b in self.batteries if b.power_w is not None]
        return sum(values) if values else None

    def battery_capacity_total(self) -> int | None:
        """Return the summed battery capacity across batteries, if known."""
        values = [b.capacity_wh for b in self.batteries if b.capacity_wh is not None]
        return sum(values) if values else None

    def effective_load_w(self) -> tuple[float | None, bool]:
        """Return household load and whether it was derived.

        If load is measured directly it is returned as-is. Otherwise it is
        derived from the power balance ``load = pv + grid - battery`` when the
        grid power is known (missing pv/battery terms are treated as zero).
        """
        if self.load.power_w is not None:
            return self.load.power_w, False
        if self.grid.power_w is None:
            return None, False
        pv = self.pv.power_w or 0.0
        battery = self.battery_power_total() or 0.0
        return self.grid.power_w + pv - battery, True

    def as_dict(self) -> dict[str, object]:
        """Serialise telemetry for entity attributes/diagnostics."""
        load_w, load_derived = self.effective_load_w()
        return {
            "grid_power_w": self.grid.power_w,
            "pv_power_w": self.pv.power_w,
            "battery_soc_average": self.battery_soc_average(),
            "battery_power_total_w": self.battery_power_total(),
            "battery_capacity_total_wh": self.battery_capacity_total(),
            "load_power_w": load_w,
            "load_derived": load_derived,
            "imbalance_price": self.imbalance_price,
            "batteries": [
                {
                    "soc": b.soc,
                    "power_w": b.power_w,
                    "capacity_wh": b.capacity_wh,
                    "temp_c": b.temp_c,
                }
                for b in self.batteries
            ],
        }


@dataclass(frozen=True, slots=True)
class SystemState:
    """Immutable snapshot combining prices and telemetry for one decision round."""

    ts: datetime
    prices: PriceSeries
    telemetry: Telemetry
