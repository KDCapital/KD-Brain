"""Build the actuator from the config entry options."""

from __future__ import annotations

from typing import Any

from ..const import CONF_BATTERY_POWER_CONTROL_ENTITY
from .base import Actuator
from .dry_run import DryRunActuator
from .entity import EntityActuator


def build_actuator(options: dict[str, Any]) -> Actuator:
    """Return an entity actuator if a control entity is set, else dry-run."""
    control_entity = options.get(CONF_BATTERY_POWER_CONTROL_ENTITY)
    if control_entity:
        return EntityActuator(control_entity)
    return DryRunActuator()
