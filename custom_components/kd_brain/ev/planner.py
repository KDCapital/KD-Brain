"""Decide the EV charge current from prices, solar surplus and target SOC."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..const import EV_GRID_VOLTAGE
from ..data.models import SystemState
from .config import EvConfig


@dataclass(frozen=True, slots=True)
class EvPlan:
    """The recommended EV charge current and the reasoning."""

    current_a: int  # 0 (off) or within [min_a, max_a]
    reason: str


@dataclass(frozen=True, slots=True)
class EvResult:
    """The outcome of one EV control round, for entities/diagnostics."""

    ts: datetime
    mode: str
    connected: bool | None
    current_a: int  # the safety-approved current
    written: bool
    reasons: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        """Serialise for entity attributes/diagnostics."""
        return {
            "ts": self.ts.isoformat(),
            "mode": self.mode,
            "connected": self.connected,
            "current_a": self.current_a,
            "written": self.written,
            "reasons": list(self.reasons),
        }


def plan_ev(state: SystemState, config: EvConfig) -> EvPlan:
    """Return the desired charge current before safety clamping."""
    if not config.enabled:
        return EvPlan(0, "EV-laden uitgeschakeld")

    ev = state.telemetry.ev
    if ev.connected is False:
        return EvPlan(0, "EV niet aangesloten")
    if ev.soc is not None and ev.soc >= config.target_soc:
        return EvPlan(0, f"EV op streef-SOC ({ev.soc:.0f}% ≥ {config.target_soc:.0f}%)")

    point = state.prices.point_at(state.ts)
    average = state.prices.average_all_in()
    if point is not None and average is not None and point.all_in < average:
        return EvPlan(config.max_a, "Prijs onder gemiddelde: laden op max stroom")

    grid = state.telemetry.grid.power_w
    if grid is not None and grid < 0:
        surplus_w = -grid + (ev.charging_power_w or 0.0)
        solar_a = int(surplus_w / (EV_GRID_VOLTAGE * config.phases))
        if solar_a >= config.min_a:
            current = min(solar_a, config.max_a)
            return EvPlan(current, f"Zonne-overschot: laden op {current} A")

    return EvPlan(0, "Geen goedkope prijs of voldoende zon")
