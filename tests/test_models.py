"""Unit tests for the immutable price models."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from custom_components.kd_brain.data.models import PricePoint, PriceSeries


def _point(hour: int, minute: int, market: float) -> PricePoint:
    start = datetime(2026, 6, 28, hour, minute, tzinfo=UTC)
    value = Decimal(str(market))
    return PricePoint(
        start=start,
        end=start + timedelta(minutes=15),
        market=value,
        all_in=value,
        feed_in=value,
    )


def _series() -> PriceSeries:
    points = (
        _point(10, 0, 0.10),
        _point(10, 15, 0.12),
        _point(10, 30, 0.14),
        _point(10, 45, 0.16),
    )
    return PriceSeries(points=points, resolution=timedelta(minutes=15))


def test_contains() -> None:
    point = _point(10, 0, 0.10)
    assert point.contains(datetime(2026, 6, 28, 10, 5, tzinfo=UTC))
    assert not point.contains(point.end)


def test_point_at_and_next() -> None:
    series = _series()
    moment = datetime(2026, 6, 28, 10, 20, tzinfo=UTC)
    current = series.point_at(moment)
    assert current is not None
    assert current.market == Decimal("0.12")
    nxt = series.next_point(moment)
    assert nxt is not None
    assert nxt.market == Decimal("0.14")


def test_min_max_average() -> None:
    series = _series()
    assert series.min_point().market == Decimal("0.10")  # type: ignore[union-attr]
    assert series.max_point().market == Decimal("0.16")  # type: ignore[union-attr]
    assert series.average_all_in() == Decimal("0.13")


def test_empty_series() -> None:
    empty = PriceSeries(points=(), resolution=timedelta(minutes=15))
    assert empty.is_empty
    assert empty.point_at(datetime(2026, 6, 28, 10, 0, tzinfo=UTC)) is None
    assert empty.min_point() is None
    assert empty.average_all_in() is None


def test_to_hourly_averages_quarters() -> None:
    hourly = _series().to_hourly()
    assert hourly.resolution == timedelta(hours=1)
    assert len(hourly.points) == 1
    point = hourly.points[0]
    assert point.market == Decimal("0.13")  # mean of 0.10, 0.12, 0.14, 0.16
    assert point.start == datetime(2026, 6, 28, 10, 0, tzinfo=UTC)
    assert point.end == datetime(2026, 6, 28, 11, 0, tzinfo=UTC)


def test_to_hourly_is_noop_for_hourly_series() -> None:
    hourly = _series().to_hourly()
    assert hourly.to_hourly() is hourly


def test_slice_local_day() -> None:
    amsterdam = ZoneInfo("Europe/Amsterdam")
    early = _point(8, 0, 0.10)  # 10:00 local on the 28th
    late = PricePoint(
        start=datetime(2026, 6, 28, 23, 30, tzinfo=UTC),  # 01:30 local on the 29th
        end=datetime(2026, 6, 28, 23, 45, tzinfo=UTC),
        market=Decimal("0.20"),
        all_in=Decimal("0.20"),
        feed_in=Decimal("0.20"),
    )
    series = PriceSeries(points=(early, late), resolution=timedelta(minutes=15))
    today = series.slice_local_day(early.start.astimezone(amsterdam).date(), amsterdam)
    assert len(today.points) == 1
    assert today.points[0] is early


def test_as_dicts() -> None:
    dicts = _series().as_dicts()
    assert len(dicts) == 4
    assert dicts[0]["market"] == 0.10
    assert "start" in dicts[0] and "end" in dicts[0]
