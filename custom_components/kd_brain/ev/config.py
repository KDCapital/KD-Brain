"""Configuration for EV smart charging."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..const import (
    CONF_CONTROL_MODE,
    CONF_ENABLE_EV,
    CONF_EV_CURRENT_CONTROL_ENTITY,
    CONF_EV_MAX_CURRENT_A,
    CONF_EV_MIN_CURRENT_A,
    CONF_EV_PHASES,
    CONF_EV_TARGET_SOC,
    CONF_MIN_DWELL_SECONDS,
    CONTROL_ACTIVE,
    DEFAULT_CONTROL_MODE,
    DEFAULT_ENABLE_EV,
    DEFAULT_EV_MAX_CURRENT_A,
    DEFAULT_EV_MIN_CURRENT_A,
    DEFAULT_EV_PHASES,
    DEFAULT_EV_TARGET_SOC,
    DEFAULT_MIN_DWELL_SECONDS,
)


@dataclass(frozen=True, slots=True)
class EvConfig:
    """User-tunable EV smart-charging configuration."""

    enabled: bool
    min_a: int
    max_a: int
    phases: int
    target_soc: float
    control_entity: str | None
    control_mode: str
    min_dwell_s: int

    @property
    def is_active(self) -> bool:
        """Return whether KD Brain may actually set the charge current."""
        return self.control_mode == CONTROL_ACTIVE

    @classmethod
    def from_options(cls, options: dict[str, Any]) -> EvConfig:
        """Build the EV config from config entry options."""
        return cls(
            enabled=bool(options.get(CONF_ENABLE_EV, DEFAULT_ENABLE_EV)),
            min_a=int(options.get(CONF_EV_MIN_CURRENT_A, DEFAULT_EV_MIN_CURRENT_A)),
            max_a=int(options.get(CONF_EV_MAX_CURRENT_A, DEFAULT_EV_MAX_CURRENT_A)),
            phases=int(options.get(CONF_EV_PHASES, DEFAULT_EV_PHASES)),
            target_soc=float(options.get(CONF_EV_TARGET_SOC, DEFAULT_EV_TARGET_SOC)),
            control_entity=options.get(CONF_EV_CURRENT_CONTROL_ENTITY),
            control_mode=options.get(CONF_CONTROL_MODE, DEFAULT_CONTROL_MODE),
            min_dwell_s=int(
                options.get(CONF_MIN_DWELL_SECONDS, DEFAULT_MIN_DWELL_SECONDS)
            ),
        )
