"""Self-consumption strategy: keep PV energy local.

Charge the battery from solar surplus, discharge it to cover household import.
This is the dominant strategy for the Netherlands once net metering ends.
"""

from __future__ import annotations

from ..data.models import SystemState
from ..engine.config import OptimizerConfig
from ..engine.decision import BatteryAction, Proposal
from .base import SELF_CONSUMPTION, battery_action, clamp_score

# Ignore tiny imbalances around zero (W).
_DEADBAND_W = 50.0


class SelfConsumptionStrategy:
    """Maximise self-consumption of solar energy."""

    @property
    def name(self) -> str:
        """Return the strategy identifier."""
        return SELF_CONSUMPTION

    def propose(self, state: SystemState, config: OptimizerConfig) -> Proposal | None:
        """Propose charging on surplus or discharging on import."""
        grid = state.telemetry.grid.power_w
        if grid is None:
            return None  # no grid telemetry -> strategy not applicable

        if grid < -_DEADBAND_W:  # exporting surplus
            surplus = -grid
            power = min(int(surplus), config.max_charge_w)
            score = clamp_score(30 + surplus / max(config.max_charge_w, 1) * 70)
            return Proposal(
                strategy=self.name,
                action=battery_action(
                    BatteryAction.CHARGE,
                    power,
                    f"PV-overschot {surplus:.0f} W: batterij laden voor zelfverbruik",
                ),
                score=score,
                rationale=f"Zonne-overschot {surplus:.0f} W beschikbaar om op te slaan",
            )

        if grid > _DEADBAND_W:  # importing from grid
            power = min(int(grid), config.max_discharge_w)
            score = clamp_score(30 + grid / max(config.max_discharge_w, 1) * 70)
            return Proposal(
                strategy=self.name,
                action=battery_action(
                    BatteryAction.DISCHARGE,
                    power,
                    f"Verbruik {grid:.0f} W uit net: ontladen i.p.v. importeren",
                ),
                score=score,
                rationale=f"Huishouden importeert {grid:.0f} W uit het net",
            )

        return Proposal(
            strategy=self.name,
            action=battery_action(BatteryAction.IDLE, 0, "PV en verbruik in balans"),
            score=20.0,
            rationale="Geen noemenswaardig overschot of tekort",
        )
