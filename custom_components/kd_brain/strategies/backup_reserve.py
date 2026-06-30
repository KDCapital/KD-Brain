"""Backup reserve strategy: keep enough charge for an outage.

When the state of charge drops below the configured reserve, the battery is
charged back up. This runs at a high priority so the reserve is protected, but
below peak shaving. The hard discharge floor itself is enforced by the safety
layer (minimum SOC).
"""

from __future__ import annotations

from ..data.models import SystemState
from ..engine.config import OptimizerConfig
from ..engine.decision import BatteryAction, Proposal
from .base import BACKUP_RESERVE, battery_action

_SCORE = 110.0


class BackupReserveStrategy:
    """Charge the battery back up to the backup reserve level."""

    @property
    def name(self) -> str:
        """Return the strategy identifier."""
        return BACKUP_RESERVE

    def propose(self, state: SystemState, config: OptimizerConfig) -> Proposal | None:
        """Propose charging while the SOC is below the reserve."""
        soc = state.telemetry.battery_soc_average()
        if soc is None or soc >= config.backup_reserve_soc:
            return None

        return Proposal(
            strategy=self.name,
            action=battery_action(
                BatteryAction.CHARGE,
                config.max_charge_w,
                f"SOC {soc:.0f}% < backup-reserve {config.backup_reserve_soc:.0f}%",
            ),
            score=_SCORE,
            rationale="Batterij opladen tot de backup-reserve",
        )
