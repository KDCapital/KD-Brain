"""Safety clamps for heat pump control (limit, throttle, anti short-cycle).

The heat pump is protected against nervous control: the offset is clamped to the
configured °C limit, writes are throttled to a minimum interval, reversing the
offset direction is blocked until a minimum dwell has elapsed (anti
short-cycling), and an unchanged offset is never re-written.

The mutable :class:`ControlState` tracks values as integer tenths of a degree so
it can be shared with the battery/EV pipelines, which are integer-based.
"""

from __future__ import annotations

from datetime import datetime

from ..const import HEATPUMP_OFFSET_STEP
from ..safety.state import ControlState
from .config import HpConfig


def to_tenths(offset_c: float) -> int:
    """Encode a °C offset as integer tenths for the shared control state."""
    return round(offset_c * 10)


def hp_safety(
    offset_c: float, config: HpConfig, state: ControlState, now: datetime
) -> tuple[float, bool, tuple[str, ...]]:
    """Clamp the requested offset and decide whether to write it.

    Returns the safety-approved offset (°C), whether it should be written, and
    the reasons for any intervention.
    """
    reasons: list[str] = []

    if offset_c > config.max_offset:
        reasons.append(f"geklemd naar +{config.max_offset:.1f} °C")
        offset_c = config.max_offset
    elif offset_c < -config.max_offset:
        reasons.append(f"geklemd naar {-config.max_offset:.1f} °C")
        offset_c = -config.max_offset

    offset_c = round(offset_c / HEATPUMP_OFFSET_STEP) * HEATPUMP_OFFSET_STEP
    tenths = to_tenths(offset_c)
    write = True

    if state.last_write_ts is not None:
        elapsed = (now - state.last_write_ts).total_seconds()
        if elapsed < config.write_throttle_s:
            write = False
            reasons.append(
                f"write-throttle: {config.write_throttle_s}s niet verstreken"
            )

    new_direction = _direction(tenths)
    if (
        write
        and new_direction not in ("idle", state.last_direction)
        and state.last_change_ts is not None
    ):
        elapsed = (now - state.last_change_ts).total_seconds()
        if elapsed < config.min_dwell_s:
            write = False
            reasons.append(
                f"anti short-cycle: min-dwell {config.min_dwell_s}s niet verstreken"
            )

    if write and state.last_written_w is not None and tenths == state.last_written_w:
        write = False
        reasons.append("ongewijzigd")

    return offset_c, write, tuple(reasons)


def _direction(tenths: int) -> str:
    """Return the offset direction label."""
    if tenths > 0:
        return "charge"
    if tenths < 0:
        return "discharge"
    return "idle"
