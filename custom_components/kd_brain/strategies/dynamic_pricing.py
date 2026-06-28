"""Dynamic pricing strategy: charge cheap, discharge expensive.

Compares the current all-in price against the series average and recommends
charging when prices are clearly below average and discharging when clearly
above.
"""

from __future__ import annotations

from decimal import Decimal

from ..data.models import SystemState
from ..engine.config import OptimizerConfig
from ..engine.decision import BatteryAction, Proposal
from .base import DYNAMIC_PRICING, battery_action, clamp_score

# Relative band around the average within which prices count as "normal".
_BAND = Decimal("0.05")


class DynamicPricingStrategy:
    """Shift battery use towards cheaper hours."""

    @property
    def name(self) -> str:
        """Return the strategy identifier."""
        return DYNAMIC_PRICING

    def propose(self, state: SystemState, config: OptimizerConfig) -> Proposal | None:
        """Propose charging below-average and discharging above-average."""
        current = state.prices.point_at(state.ts)
        average = state.prices.average_all_in()
        if current is None or average is None or average <= 0:
            return None

        price = current.all_in
        deviation = (average - price) / average  # > 0 cheaper than average

        if price < average * (Decimal(1) - _BAND):
            score = clamp_score(float(deviation) * 300)
            return Proposal(
                strategy=self.name,
                action=battery_action(
                    BatteryAction.CHARGE,
                    config.max_charge_w,
                    f"Prijs €{price:.3f} < gemiddelde €{average:.3f}: goedkoop laden",
                ),
                score=score,
                rationale=f"Prijs {float(deviation) * 100:.0f}% onder gemiddelde",
            )

        if price > average * (Decimal(1) + _BAND):
            score = clamp_score(float(-deviation) * 300)
            return Proposal(
                strategy=self.name,
                action=battery_action(
                    BatteryAction.DISCHARGE,
                    config.max_discharge_w,
                    f"Prijs €{price:.3f} boven gemiddelde €{average:.3f}: ontladen",
                ),
                score=score,
                rationale=f"Prijs {float(-deviation) * 100:.0f}% boven gemiddelde",
            )

        return Proposal(
            strategy=self.name,
            action=battery_action(BatteryAction.IDLE, 0, "Prijs rond het gemiddelde"),
            score=15.0,
            rationale="Geen duidelijk prijsvoordeel om nu te handelen",
        )
