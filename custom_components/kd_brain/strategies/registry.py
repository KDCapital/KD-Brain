"""Build the set of enabled strategies from the engine configuration."""

from __future__ import annotations

from ..engine.config import OptimizerConfig
from .arbitrage import ArbitrageStrategy
from .base import Strategy
from .dynamic_pricing import DynamicPricingStrategy
from .self_consumption import SelfConsumptionStrategy


def enabled_strategies(config: OptimizerConfig) -> list[Strategy]:
    """Return the enabled strategy instances, in priority order."""
    strategies: list[Strategy] = []
    if config.self_consumption:
        strategies.append(SelfConsumptionStrategy())
    if config.dynamic_pricing:
        strategies.append(DynamicPricingStrategy())
    if config.arbitrage:
        strategies.append(ArbitrageStrategy())
    return strategies
