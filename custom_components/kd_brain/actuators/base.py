"""Actuator protocol and the actuation result model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol, runtime_checkable

from homeassistant.core import HomeAssistant

from ..engine.decision import Action
from ..safety.gate import SafetyOutcome


@runtime_checkable
class Actuator(Protocol):
    """Executes a signed battery power setpoint on a device."""

    @property
    def name(self) -> str:
        """Stable identifier for the actuator."""

    @property
    def is_configured(self) -> bool:
        """Return whether the actuator can actually write."""

    async def async_apply(self, hass: HomeAssistant, signed_w: int) -> None:
        """Apply a signed power (+ charge, - discharge, 0 idle)."""


@dataclass(frozen=True, slots=True)
class ActuationResult:
    """The result of one actuation round, for entities/diagnostics."""

    ts: datetime
    mode: str
    intended: Action
    outcome: SafetyOutcome
    written: bool

    @property
    def intervened(self) -> bool:
        """Return whether safety changed or blocked the intended action."""
        return self.outcome.action.action is not self.intended.action or bool(
            self.outcome.reasons
        )

    def as_dict(self) -> dict[str, Any]:
        """Serialise for entity attributes/diagnostics."""
        return {
            "ts": self.ts.isoformat(),
            "mode": self.mode,
            "written": self.written,
            "intended": self.intended.as_dict(),
            "outcome": self.outcome.as_dict(),
        }
