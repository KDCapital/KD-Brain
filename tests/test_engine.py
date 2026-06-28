"""Unit tests for the engine: strategies, optimiser and decision model."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from custom_components.kd_brain.data.models import (
    BatteryState,
    GridState,
    PricePoint,
    PriceSeries,
    SystemState,
    Telemetry,
)
from custom_components.kd_brain.engine.config import OptimizerConfig
from custom_components.kd_brain.engine.decision import BatteryAction
from custom_components.kd_brain.engine.optimizer import optimize
from custom_components.kd_brain.strategies.arbitrage import ArbitrageStrategy
from custom_components.kd_brain.strategies.dynamic_pricing import DynamicPricingStrategy
from custom_components.kd_brain.strategies.self_consumption import (
    SelfConsumptionStrategy,
)

NOW = datetime(2026, 6, 28, 10, 0, tzinfo=UTC)
_EMPTY_TELEMETRY = Telemetry()


def _point(hour: int, market: float) -> PricePoint:
    start = datetime(2026, 6, 28, hour, 0, tzinfo=UTC)
    value = Decimal(str(market))
    return PricePoint(start, start + timedelta(hours=1), value, value, value)


def _series(*pairs: tuple[int, float]) -> PriceSeries:
    return PriceSeries(
        points=tuple(_point(h, m) for h, m in pairs), resolution=timedelta(hours=1)
    )


def _config(**overrides: object) -> OptimizerConfig:
    return replace(OptimizerConfig.from_options({}), **overrides)


def _state(prices: PriceSeries, telemetry: Telemetry = _EMPTY_TELEMETRY) -> SystemState:
    return SystemState(ts=NOW, prices=prices, telemetry=telemetry)


# --- Self-consumption ------------------------------------------------------


def test_self_consumption_charges_on_surplus() -> None:
    state = _state(_series((10, 0.2)), Telemetry(grid=GridState(power_w=-1000.0)))
    proposal = SelfConsumptionStrategy().propose(state, _config())
    assert proposal is not None
    assert proposal.action.action is BatteryAction.CHARGE


def test_self_consumption_discharges_on_import() -> None:
    state = _state(_series((10, 0.2)), Telemetry(grid=GridState(power_w=1000.0)))
    proposal = SelfConsumptionStrategy().propose(state, _config())
    assert proposal is not None
    assert proposal.action.action is BatteryAction.DISCHARGE


def test_self_consumption_abstains_without_grid() -> None:
    proposal = SelfConsumptionStrategy().propose(_state(_series((10, 0.2))), _config())
    assert proposal is None


# --- Dynamic pricing -------------------------------------------------------


def test_dynamic_pricing_charges_when_cheap() -> None:
    state = _state(_series((10, 0.10), (11, 0.30), (12, 0.30)))
    proposal = DynamicPricingStrategy().propose(state, _config())
    assert proposal is not None
    assert proposal.action.action is BatteryAction.CHARGE


def test_dynamic_pricing_discharges_when_expensive() -> None:
    state = _state(_series((10, 0.30), (11, 0.10), (12, 0.10)))
    proposal = DynamicPricingStrategy().propose(state, _config())
    assert proposal is not None
    assert proposal.action.action is BatteryAction.DISCHARGE


# --- Arbitrage -------------------------------------------------------------


def test_arbitrage_charges_when_profitable() -> None:
    state = _state(_series((10, 0.10), (11, 0.40)))
    proposal = ArbitrageStrategy().propose(state, _config())
    assert proposal is not None
    assert proposal.action.action is BatteryAction.CHARGE


def test_arbitrage_idle_when_spread_too_small() -> None:
    state = _state(_series((10, 0.20), (11, 0.22)))
    proposal = ArbitrageStrategy().propose(state, _config())
    assert proposal is not None
    assert proposal.action.action is BatteryAction.IDLE


def test_arbitrage_profit_accounts_for_costs() -> None:
    config = _config()
    # 0.40 - 0.10/0.9 - 0.05 - 0.02 = 0.2189
    assert config.arbitrage_profit(Decimal("0.10"), Decimal("0.40")) > 0
    assert config.arbitrage_profit(Decimal("0.20"), Decimal("0.22")) < 0


# --- Optimiser -------------------------------------------------------------


def test_optimizer_picks_highest_score() -> None:
    state = _state(_series((10, 0.2)), Telemetry(grid=GridState(power_w=-2000.0)))
    decision = optimize(state, _config())
    assert decision.chosen.action is BatteryAction.CHARGE
    assert decision.strategy == "self_consumption"
    assert decision.considered  # non-empty
    assert "self_consumption" in decision.why


def test_optimizer_rejects_charge_when_battery_full() -> None:
    telemetry = Telemetry(
        grid=GridState(power_w=-2000.0),
        batteries=(BatteryState(soc=96.0),),
    )
    decision = optimize(_state(_series((10, 0.2)), telemetry), _config())
    assert decision.chosen.action is BatteryAction.IDLE
    reasons = dict(decision.rejected)
    assert "self_consumption" in reasons
    assert "vol" in reasons["self_consumption"]


def test_optimizer_no_strategies_enabled() -> None:
    config = _config(self_consumption=False, dynamic_pricing=False, arbitrage=False)
    decision = optimize(_state(_series((10, 0.2))), config)
    assert decision.chosen.action is BatteryAction.IDLE
    assert decision.strategy == "none"


def test_decision_serialisation() -> None:
    state = _state(_series((10, 0.2)), Telemetry(grid=GridState(power_w=-1000.0)))
    data = optimize(state, _config()).as_dict()
    assert set(data) >= {
        "created",
        "mode",
        "action",
        "strategy",
        "why",
        "considered",
        "rejected",
    }
    assert data["mode"] == "observe_only"
