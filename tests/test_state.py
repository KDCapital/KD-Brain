"""Tests for the SystemState builder."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from custom_components.kd_brain.data.models import PriceSeries, Telemetry
from custom_components.kd_brain.engine.state import build_system_state


def test_build_system_state() -> None:
    prices = PriceSeries(points=(), resolution=timedelta(minutes=15))
    telemetry = Telemetry()
    now = datetime(2026, 6, 28, 10, 0, tzinfo=UTC)

    state = build_system_state(now, prices, telemetry)

    assert state.ts == now
    assert state.prices is prices
    assert state.telemetry is telemetry
