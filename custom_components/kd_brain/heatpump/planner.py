"""Decide the heat pump setpoint offset from the price curve.

The heat pump keeps running under its own thermostat; KD Brain only nudges the
target temperature (a *stooklijnverschuiving*) up a little when electricity is
cheap and down when it is expensive, shifting demand towards cheap hours without
sacrificing comfort. The offset is a small signed number of degrees Celsius.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..const import HEATPUMP_GAIN, HEATPUMP_OFFSET_STEP
from ..data.models import SystemState
from .config import HpConfig


@dataclass(frozen=True, slots=True)
class HpPlan:
    """The recommended setpoint offset (°C) and the reasoning."""

    offset_c: float  # within [-max_offset, +max_offset]
    reason: str


@dataclass(frozen=True, slots=True)
class HpResult:
    """The outcome of one heat pump control round, for entities/diagnostics."""

    ts: datetime
    mode: str
    power_w: float | None
    offset_c: float  # the safety-approved offset
    written: bool
    reasons: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        """Serialise for entity attributes/diagnostics."""
        return {
            "ts": self.ts.isoformat(),
            "mode": self.mode,
            "power_w": self.power_w,
            "offset_c": self.offset_c,
            "written": self.written,
            "reasons": list(self.reasons),
        }


def _round_step(value: float, step: float) -> float:
    """Round ``value`` to the nearest multiple of ``step``."""
    return round(value / step) * step


def plan_heatpump(state: SystemState, config: HpConfig) -> HpPlan:
    """Return the desired setpoint offset before safety clamping.

    A negative ``ratio`` (price above average) yields a negative offset (heat
    less now); a positive ``ratio`` (price below average) yields a positive
    offset (pre-heat while cheap). The gain amplifies moderate deviations so the
    offset saturates to the configured limit on clearly cheap/expensive hours.
    """
    if not config.enabled:
        return HpPlan(0.0, "Warmtepomp-optimalisatie uitgeschakeld")

    point = state.prices.point_at(state.ts)
    average = state.prices.average_all_in()
    if point is None or average is None or average == 0:
        return HpPlan(0.0, "Geen prijsinformatie beschikbaar")

    ratio = float((average - point.all_in) / average)
    raw = ratio * HEATPUMP_GAIN * config.max_offset
    clamped = max(-config.max_offset, min(config.max_offset, raw))
    offset = _round_step(clamped, HEATPUMP_OFFSET_STEP)

    if offset > 0:
        reason = f"Prijs onder gemiddelde: voorverwarmen (+{offset:.1f} °C)"
    elif offset < 0:
        reason = f"Prijs boven gemiddelde: uitstellen ({offset:.1f} °C)"
    else:
        reason = "Prijs rond gemiddelde: geen verschuiving"
    return HpPlan(offset, reason)
