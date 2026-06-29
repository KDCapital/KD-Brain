"""Configuration for the safety layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..const import (
    CONF_BATTERY_MAX_SOC,
    CONF_BATTERY_MIN_SOC,
    CONF_BATTERY_POWER_CONTROL_ENTITY,
    CONF_CONTROL_MODE,
    CONF_HYSTERESIS_W,
    CONF_MAX_CHARGE_POWER_W,
    CONF_MAX_DISCHARGE_POWER_W,
    CONF_MIN_DWELL_SECONDS,
    CONF_WRITE_THROTTLE_SECONDS,
    CONTROL_ACTIVE,
    DEFAULT_BATTERY_MAX_SOC,
    DEFAULT_BATTERY_MIN_SOC,
    DEFAULT_CONTROL_MODE,
    DEFAULT_HYSTERESIS_W,
    DEFAULT_MAX_CHARGE_POWER_W,
    DEFAULT_MAX_DISCHARGE_POWER_W,
    DEFAULT_MIN_DWELL_SECONDS,
    DEFAULT_WRITE_THROTTLE_SECONDS,
)


@dataclass(frozen=True, slots=True)
class SafetyConfig:
    """User-tunable safety and control parameters."""

    control_mode: str
    control_entity: str | None
    battery_min_soc: float
    battery_max_soc: float
    max_charge_w: int
    max_discharge_w: int
    write_throttle_s: int
    min_dwell_s: int
    hysteresis_w: int

    @property
    def is_active(self) -> bool:
        """Return whether KD Brain is allowed to steer hardware."""
        return self.control_mode == CONTROL_ACTIVE

    @classmethod
    def from_options(cls, options: dict[str, Any]) -> SafetyConfig:
        """Build the safety config from config entry options."""
        return cls(
            control_mode=options.get(CONF_CONTROL_MODE, DEFAULT_CONTROL_MODE),
            control_entity=options.get(CONF_BATTERY_POWER_CONTROL_ENTITY),
            battery_min_soc=float(
                options.get(CONF_BATTERY_MIN_SOC, DEFAULT_BATTERY_MIN_SOC)
            ),
            battery_max_soc=float(
                options.get(CONF_BATTERY_MAX_SOC, DEFAULT_BATTERY_MAX_SOC)
            ),
            max_charge_w=int(
                options.get(CONF_MAX_CHARGE_POWER_W, DEFAULT_MAX_CHARGE_POWER_W)
            ),
            max_discharge_w=int(
                options.get(CONF_MAX_DISCHARGE_POWER_W, DEFAULT_MAX_DISCHARGE_POWER_W)
            ),
            write_throttle_s=int(
                options.get(CONF_WRITE_THROTTLE_SECONDS, DEFAULT_WRITE_THROTTLE_SECONDS)
            ),
            min_dwell_s=int(
                options.get(CONF_MIN_DWELL_SECONDS, DEFAULT_MIN_DWELL_SECONDS)
            ),
            hysteresis_w=int(options.get(CONF_HYSTERESIS_W, DEFAULT_HYSTERESIS_W)),
        )
