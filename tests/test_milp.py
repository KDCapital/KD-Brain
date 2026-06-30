"""Tests for the optional MILP optimiser.

The solve path requires the optional ``highspy`` package, so this module is
skipped when it is not installed (e.g. in CI). The graceful fallback when
highspy is missing is covered in ``test_optimization.py``.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from custom_components.kd_brain.data.models import (
    BatteryState,
    PricePoint,
    PriceSeries,
    SystemState,
    Telemetry,
)
from custom_components.kd_brain.engine.config import OptimizerConfig
from custom_components.kd_brain.engine.decision import BatteryAction
from custom_components.kd_brain.engine.milp import milp_optimize

pytest.importorskip("highspy")

NOW = datetime(2026, 6, 28, 10, 0, tzinfo=UTC)


def _point(hour: int, market: float) -> PricePoint:
    start = datetime(2026, 6, 28, hour, 0, tzinfo=UTC)
    value = Decimal(str(market))
    return PricePoint(start, start + timedelta(hours=1), value, value, value)


def _state(soc: float | None) -> SystemState:
    prices = PriceSeries(
        points=(_point(10, 0.10), _point(11, 0.10), _point(12, 0.40), _point(13, 0.40)),
        resolution=timedelta(hours=1),
    )
    batteries = (BatteryState(soc=soc, capacity_wh=5000),) if soc is not None else ()
    return SystemState(ts=NOW, prices=prices, telemetry=Telemetry(batteries=batteries))


def _config(**overrides: object) -> OptimizerConfig:
    return replace(OptimizerConfig.from_options({}), **overrides)


def test_milp_charges_when_cheap_now_expensive_later() -> None:
    decision = milp_optimize(_state(soc=30.0), _config())
    assert decision is not None
    assert decision.strategy == "milp"
    assert decision.chosen.action is BatteryAction.CHARGE


def test_milp_returns_none_without_capacity() -> None:
    # No batteries configured -> no capacity -> cannot build the model.
    assert milp_optimize(_state(soc=None), _config()) is None
