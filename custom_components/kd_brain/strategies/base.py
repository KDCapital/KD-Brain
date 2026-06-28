"""Strategy protocol and shared helpers."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..data.models import SystemState
from ..engine.config import OptimizerConfig
from ..engine.decision import Action, BatteryAction, Proposal

# Strategy identifiers (also used as translation keys / option names).
SELF_CONSUMPTION = "self_consumption"
DYNAMIC_PRICING = "dynamic_pricing"
ARBITRAGE = "arbitrage"


@runtime_checkable
class Strategy(Protocol):
    """A pluggable decision strategy."""

    @property
    def name(self) -> str:
        """Stable identifier for the strategy."""

    def propose(self, state: SystemState, config: OptimizerConfig) -> Proposal | None:
        """Return a scored proposal, or None when the strategy does not apply."""


def battery_action(action: BatteryAction, power_w: int, reason: str) -> Action:
    """Build a battery action."""
    return Action(device="battery", action=action, power_w=power_w, reason=reason)


def clamp_score(value: float) -> float:
    """Clamp a score into the 0-100 range."""
    return max(0.0, min(100.0, value))
