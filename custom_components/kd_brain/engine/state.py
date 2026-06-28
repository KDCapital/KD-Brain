"""Build immutable :class:`SystemState` snapshots for the engine.

Combining all inputs into one frozen snapshot per round is what keeps the
later optimisation pipeline deterministic and free of races between async
data updates.
"""

from __future__ import annotations

from datetime import datetime

from ..data.models import PriceSeries, SystemState, Telemetry


def build_system_state(
    now: datetime, prices: PriceSeries, telemetry: Telemetry
) -> SystemState:
    """Assemble a snapshot from the latest prices and telemetry."""
    return SystemState(ts=now, prices=prices, telemetry=telemetry)
