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
