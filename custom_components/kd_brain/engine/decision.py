"""Explainable decision model for the KD Brain engine.

Every optimisation round produces a :class:`Decision` that records not just the
chosen action, but *why* it was chosen, which strategies were considered, their
scores, and why the alternatives were rejected. This is a first-class output so
users can always understand and trust the recommendation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any


class BatteryAction(StrEnum):
    """Recommended battery action."""

    IDLE = "idle"
    CHARGE = "charge"
    DISCHARGE = "discharge"


@dataclass(frozen=True, slots=True)
class Action:
    """A concrete recommended action for a device."""

    device: str  # "battery" in M3
    action: BatteryAction
    power_w: int  # magnitude; 0 for idle
    reason: str

    def as_dict(self) -> dict[str, Any]:
        """Serialise for entity attributes."""
        return {
            "device": self.device,
            "action": self.action.value,
            "power_w": self.power_w,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class Proposal:
    """A strategy's suggested action plus its score and rationale."""

    strategy: str
    action: Action
    score: float  # higher is more preferred (already weighted)
    rationale: str

    def as_dict(self) -> dict[str, Any]:
        """Serialise for entity attributes."""
        return {
            "strategy": self.strategy,
            "action": self.action.action.value,
            "power_w": self.action.power_w,
            "score": round(self.score, 2),
            "rationale": self.rationale,
        }


@dataclass(frozen=True, slots=True)
class Decision:
    """The outcome of one optimisation round, with full explanation."""

    created: datetime
    mode: str
    chosen: Action
    strategy: str
    why: str
    considered: tuple[Proposal, ...]
    rejected: tuple[tuple[str, str], ...]  # (strategy, reason)

    def as_dict(self) -> dict[str, Any]:
        """Serialise the full decision for entity attributes/diagnostics."""
        return {
            "created": self.created.isoformat(),
            "mode": self.mode,
            "action": self.chosen.action.value,
            "power_w": self.chosen.power_w,
            "strategy": self.strategy,
            "why": self.why,
            "considered": [p.as_dict() for p in self.considered],
            "rejected": [
                {"strategy": name, "reason": reason} for name, reason in self.rejected
            ],
        }
