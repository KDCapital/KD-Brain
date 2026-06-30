"""Safety clamps for EV charging (IEC 61851, anti-oscillation)."""

from __future__ import annotations

from datetime import datetime

from ..safety.state import ControlState
from .config import EvConfig


def ev_safety(
    current_a: int, config: EvConfig, state: ControlState, now: datetime
) -> tuple[int, bool, tuple[str, ...]]:
    """Clamp the requested current and decide whether to write it.

    Enforces IEC 61851 (a charge current is either 0 or at least the minimum,
    never in between), the maximum current, and anti-oscillation: turning on is
    not allowed again before the minimum dwell time has elapsed. Turning off is
    always permitted.
    """
    reasons: list[str] = []

    if 0 < current_a < config.min_a:
        reasons.append(f"IEC 61851: {current_a} A < min {config.min_a} A → uit")
        current_a = 0
    if current_a > config.max_a:
        reasons.append(f"geklemd naar {config.max_a} A")
        current_a = config.max_a

    new_direction = "charge" if current_a > 0 else "idle"
    write = True

    if (
        new_direction not in ("idle", state.last_direction)
        and state.last_change_ts is not None
    ):
        elapsed = (now - state.last_change_ts).total_seconds()
        if elapsed < config.min_dwell_s:
            write = False
            reasons.append(
                f"anti-oscillatie: min-dwell {config.min_dwell_s}s niet verstreken"
            )

    if write and state.last_written_w is not None and current_a == state.last_written_w:
        write = False
        reasons.append("ongewijzigd")

    return current_a, write, tuple(reasons)
