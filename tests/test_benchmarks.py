"""Runtime benchmarks for the optimisation engine.

These are not micro-benchmarks with statistical rigour; they are regression
guards that fail loudly if the heuristic or MILP optimiser gets accidentally
quadratic (or worse) over a realistic 48-hour, 15-minute-resolution horizon.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import time

import pytest

from custom_components.kd_brain.data.models import (
    BatteryState,
    PricePoint,
    PriceSeries,
    SystemState,
    Telemetry,
)
from custom_components.kd_brain.engine.config import OptimizerConfig
from custom_components.kd_brain.engine.optimizer import optimize

NOW = datetime(2026, 6, 28, 10, 0, tzinfo=UTC)
HORIZON_HOURS = 48
RESOLUTION = timedelta(minutes=15)


def _price_series() -> PriceSeries:
    """Build a 48-hour, 15-minute-resolution price curve with a daily cycle."""
    points: list[PricePoint] = []
    steps = int(HORIZON_HOURS * timedelta(hours=1) / RESOLUTION)
    for i in range(steps):
        start = NOW + i * RESOLUTION
        # A simple sinusoidal-ish daily price cycle, always positive.
        cents = 10 + (i % 96)
        value = Decimal(cents) / Decimal(100)
        points.append(PricePoint(start, start + RESOLUTION, value, value, value))
    return PriceSeries(points=tuple(points), resolution=RESOLUTION)


def _state() -> SystemState:
    batteries = (BatteryState(soc=50.0, capacity_wh=10000),)
    return SystemState(
        ts=NOW, prices=_price_series(), telemetry=Telemetry(batteries=batteries)
    )


def _config(**overrides: object) -> OptimizerConfig:
    return replace(OptimizerConfig.from_options({}), **overrides)


def test_heuristic_optimizer_runtime_bounded() -> None:
    """The heuristic optimiser must stay fast regardless of horizon length."""
    state = _state()
    config = _config()

    start = time.perf_counter()
    for _ in range(50):
        optimize(state, config)
    elapsed = time.perf_counter() - start

    assert elapsed < 1.0, f"50 heuristic rounds took {elapsed:.3f}s (budget: 1.0s)"


def test_milp_optimizer_runtime_bounded() -> None:
    """The optional MILP solver must solve a 48h/15min horizon quickly."""
    pytest.importorskip("highspy")
    from custom_components.kd_brain.engine.milp import (  # noqa: PLC0415
        milp_optimize,
    )

    state = _state()
    config = _config()

    start = time.perf_counter()
    decision = milp_optimize(state, config)
    elapsed = time.perf_counter() - start

    assert decision is not None
    assert elapsed < 5.0, f"MILP solve over {HORIZON_HOURS}h took {elapsed:.3f}s"
