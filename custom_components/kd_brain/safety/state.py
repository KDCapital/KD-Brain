"""Mutable control state used by the safety layer between actuations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


def direction(signed_w: int) -> str:
    """Return the direction label for a signed power (+ charge, - discharge)."""
    if signed_w > 0:
        return "charge"
    if signed_w < 0:
        return "discharge"
    return "idle"


@dataclass(slots=True)
class ControlState:
    """Tracks the last actuation so the gate can throttle and damp oscillation."""

    last_written_w: int | None = None
    last_write_ts: datetime | None = None
    last_direction: str = "idle"
    last_change_ts: datetime | None = None

    def record(self, signed_w: int, now: datetime) -> None:
        """Record a successful write."""
        new_direction = direction(signed_w)
        if new_direction != self.last_direction:
            self.last_change_ts = now
            self.last_direction = new_direction
        self.last_written_w = signed_w
        self.last_write_ts = now
