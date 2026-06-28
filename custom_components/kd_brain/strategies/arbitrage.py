"""Arbitrage strategy: charge now only if it is economically worthwhile.

Looks ahead over the remaining price horizon and recommends charging only when
the best future price beats the cost of charging now, after round-trip losses,
battery degradation and a safety margin. This is the explicit economic model the
design requires -- not a simple if-statement.
"""

from __future__ import annotations

from ..data.models import SystemState
from ..engine.config import OptimizerConfig
from ..engine.decision import BatteryAction, Proposal
from .base import ARBITRAGE, battery_action, clamp_score

# A strongly profitable arbitrage should outrank the other strategies.
_PRIORITY = 1.2


class ArbitrageStrategy:
    """Charge when the look-ahead spread covers all costs."""

    @property
    def name(self) -> str:
        """Return the strategy identifier."""
        return ARBITRAGE

    def propose(self, state: SystemState, config: OptimizerConfig) -> Proposal | None:
        """Propose charging when a profitable future price exists."""
        current = state.prices.point_at(state.ts)
        upcoming = [p for p in state.prices.points if p.start > state.ts]
        if current is None or not upcoming:
            return None

        buy = current.all_in
        best = max(upcoming, key=lambda p: p.all_in)
        profit = config.arbitrage_profit(buy, best.all_in)
        hours_ahead = (best.start - state.ts).total_seconds() / 3600

        if profit > 0:
            score = clamp_score(float(profit) * 1000) * _PRIORITY
            return Proposal(
                strategy=self.name,
                action=battery_action(
                    BatteryAction.CHARGE,
                    config.max_charge_w,
                    (
                        f"Arbitrage: nu €{buy:.3f} laden, ~{hours_ahead:.1f}u later "
                        f"à €{best.all_in:.3f}, netto €{profit:.3f}/kWh"
                    ),
                ),
                score=score,
                rationale=(
                    f"Spread dekt degradatie + verliezen + marge "
                    f"(netto €{profit:.3f}/kWh)"
                ),
            )

        return Proposal(
            strategy=self.name,
            action=battery_action(BatteryAction.IDLE, 0, "Geen rendabele arbitrage"),
            score=5.0,
            rationale=(
                f"Beste spread levert €{profit:.3f}/kWh op na kosten: niet rendabel"
            ),
        )
