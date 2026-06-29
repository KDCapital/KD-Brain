"""The safety gate: validates and clamps an action before it can be actuated.

This is a pure function over the intended action, the latest telemetry and the
control state. It returns the action that is actually allowed (possibly clamped
to idle or to a lower power), whether a write should happen at all, and a list
of human-readable reasons for any clamp/hold so the user can see what the safety
layer did.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..data.models import Telemetry
from ..engine.decision import Action, BatteryAction
from .config import SafetyConfig
from .state import ControlState, direction


@dataclass(frozen=True, slots=True)
class SafetyOutcome:
    """Result of running an action through the safety gate."""

    action: Action  # clamped action that is allowed
    signed_w: int  # + charge, - discharge, 0 idle
    write: bool  # whether the actuator should write now
    reasons: tuple[str, ...]  # clamps/holds the gate applied

    def as_dict(self) -> dict[str, Any]:
        """Serialise for entity attributes/diagnostics."""
        return {
            "action": self.action.action.value,
            "signed_w": self.signed_w,
            "write": self.write,
            "reasons": list(self.reasons),
        }


def _as_action(signed_w: int, reason: str) -> Action:
    """Build a battery Action from a signed power."""
    if signed_w > 0:
        kind = BatteryAction.CHARGE
    elif signed_w < 0:
        kind = BatteryAction.DISCHARGE
    else:
        kind = BatteryAction.IDLE
    return Action(device="battery", action=kind, power_w=abs(signed_w), reason=reason)


def evaluate(
    intended: Action,
    telemetry: Telemetry,
    state: ControlState,
    config: SafetyConfig,
    now: datetime,
) -> SafetyOutcome:
    """Clamp/validate ``intended`` and decide whether to write now."""
    reasons: list[str] = []
    kind = intended.action
    soc = telemetry.battery_soc_average()

    # 1. State-of-charge limits (hard block).
    if (
        kind is BatteryAction.CHARGE
        and soc is not None
        and soc >= config.battery_max_soc
    ):
        reasons.append(
            f"SOC {soc:.0f}% ≥ max {config.battery_max_soc:.0f}%: laden geblokkeerd"
        )
        kind = BatteryAction.IDLE
    elif (
        kind is BatteryAction.DISCHARGE
        and soc is not None
        and soc <= config.battery_min_soc
    ):
        reasons.append(
            f"SOC {soc:.0f}% ≤ min {config.battery_min_soc:.0f}%: ontladen geblokkeerd"
        )
        kind = BatteryAction.IDLE

    # 2. Power clamp.
    if kind is BatteryAction.CHARGE:
        power = min(intended.power_w, config.max_charge_w)
        signed = power
    elif kind is BatteryAction.DISCHARGE:
        power = min(intended.power_w, config.max_discharge_w)
        signed = -power
    else:
        signed = 0
    if kind is not BatteryAction.IDLE and abs(signed) != intended.power_w:
        reasons.append(f"vermogen geklemd naar {abs(signed)} W")

    new_direction = direction(signed)
    write = True

    # 3. Anti-oscillation: do not reverse direction before the min dwell time.
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

    # 4. Write-throttle (idle/stop is always allowed through immediately).
    if write and signed != 0 and state.last_write_ts is not None:
        elapsed = (now - state.last_write_ts).total_seconds()
        if elapsed < config.write_throttle_s:
            write = False
            reasons.append(f"write-throttle: {config.write_throttle_s}s actief")

    # 5. No-write-if-unchanged (within hysteresis).
    if (
        write
        and state.last_written_w is not None
        and new_direction == state.last_direction
        and abs(signed - state.last_written_w) <= config.hysteresis_w
    ):
        write = False
        reasons.append(f"ongewijzigd (binnen hysterese {config.hysteresis_w} W)")

    return SafetyOutcome(
        action=_as_action(signed, intended.reason),
        signed_w=signed,
        write=write,
        reasons=tuple(reasons),
    )
