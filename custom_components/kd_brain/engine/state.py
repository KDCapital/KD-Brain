"""Build immutable :class:`SystemState` snapshots for the engine.

Combining all inputs into one frozen snapshot per round is what keeps the
later optimisation pipeline deterministic and free of races between async
data updates.
"""

from __future__ import annotations

from datetime import datetime

from ..data.models import Forecast, PriceSeries, SystemState, Telemetry

_EMPTY_FORECAST = Forecast()


def build_system_state(
    now: datetime,
    prices: PriceSeries,
    telemetry: Telemetry,
    forecast: Forecast = _EMPTY_FORECAST,
) -> SystemState:
    """Assemble a snapshot from the latest prices, telemetry and forecast."""
    return SystemState(ts=now, prices=prices, telemetry=telemetry, forecast=forecast)
