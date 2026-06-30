"""Peak shaving strategy: cap grid import/export at a configured threshold.

Relevant for capacity-based and time-dependent grid tariffs (NL 2029). When the
grid import exceeds the threshold, the battery discharges to shave the peak;
when export exceeds the threshold, it charges to absorb the surplus. This is a
high-priority strategy: avoiding a peak usually outweighs price optimisation.
"""

from __future__ import annotations

from ..data.models import SystemState
from ..engine.config import OptimizerConfig
from ..engine.decision import BatteryAction, Proposal
from .base import PEAK_SHAVING, battery_action

# Base score so peak shaving outranks the price/self-consumption strategies.
_BASE_SCORE = 130.0


class PeakShavingStrategy:
    """Shave grid import/export peaks with the battery."""

    @property
    def name(self) -> str:
        """Return the strategy identifier."""
        return PEAK_SHAVING

    def propose(self, state: SystemState, config: OptimizerConfig) -> Proposal | None:
        """Discharge above the import peak, charge above the export peak."""
        grid = state.telemetry.grid.power_w
        if grid is None:
            return None

        if grid > config.peak_import_w:
            excess = grid - config.peak_import_w
            power = min(int(excess), config.max_discharge_w)
            return Proposal(
                strategy=self.name,
                action=battery_action(
                    BatteryAction.DISCHARGE,
                    power,
                    f"Piek-import {grid:.0f} W > {config.peak_import_w} W: piek kappen",
                ),
                score=_BASE_SCORE + min(excess / 50, 50),
                rationale=f"Netimport {excess:.0f} W boven de piekgrens",
            )

        if grid < -config.peak_export_w:
            excess = -grid - config.peak_export_w
            power = min(int(excess), config.max_charge_w)
            return Proposal(
                strategy=self.name,
                action=battery_action(
                    BatteryAction.CHARGE,
                    power,
                    f"Piek-export {-grid:.0f} W > {config.peak_export_w} W: opslaan",
                ),
                score=_BASE_SCORE + min(excess / 50, 50),
                rationale=f"Teruglevering {excess:.0f} W boven de piekgrens",
            )

        return None  # within limits: peak shaving not applicable
