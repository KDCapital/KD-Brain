"""Configuration for heat pump optimization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..const import (
    CONF_CONTROL_MODE,
    CONF_ENABLE_HEATPUMP,
    CONF_HEATPUMP_MAX_OFFSET,
    CONF_HEATPUMP_OFFSET_CONTROL_ENTITY,
    CONF_MIN_DWELL_SECONDS,
    CONF_WRITE_THROTTLE_SECONDS,
    CONTROL_ACTIVE,
    DEFAULT_CONTROL_MODE,
    DEFAULT_ENABLE_HEATPUMP,
    DEFAULT_HEATPUMP_MAX_OFFSET,
    DEFAULT_MIN_DWELL_SECONDS,
    DEFAULT_WRITE_THROTTLE_SECONDS,
)


@dataclass(frozen=True, slots=True)
class HpConfig:
    """User-tunable heat pump optimization configuration."""

    enabled: bool
    max_offset: float  # °C, absolute setpoint-offset limit
    control_entity: str | None
    control_mode: str
    write_throttle_s: int
    min_dwell_s: int

    @property
    def is_active(self) -> bool:
        """Return whether KD Brain may actually write the setpoint offset."""
        return self.control_mode == CONTROL_ACTIVE

    @classmethod
    def from_options(cls, options: dict[str, Any]) -> HpConfig:
        """Build the heat pump config from config entry options."""
        return cls(
            enabled=bool(options.get(CONF_ENABLE_HEATPUMP, DEFAULT_ENABLE_HEATPUMP)),
            max_offset=float(
                options.get(CONF_HEATPUMP_MAX_OFFSET, DEFAULT_HEATPUMP_MAX_OFFSET)
            ),
            control_entity=options.get(CONF_HEATPUMP_OFFSET_CONTROL_ENTITY),
            control_mode=options.get(CONF_CONTROL_MODE, DEFAULT_CONTROL_MODE),
            write_throttle_s=int(
                options.get(CONF_WRITE_THROTTLE_SECONDS, DEFAULT_WRITE_THROTTLE_SECONDS)
            ),
            min_dwell_s=int(
                options.get(CONF_MIN_DWELL_SECONDS, DEFAULT_MIN_DWELL_SECONDS)
            ),
        )
