"""Forecasting interface (AI-ready) and a default entity-based implementation.

A :class:`Forecaster` turns the current Home Assistant state into a
:class:`~custom_components.kd_brain.data.models.Forecast`. The default
:class:`EntityForecaster` reads an external PV-forecast integration (e.g.
Forecast.Solar). The protocol is the seam where a machine-learning forecaster
can later be plugged in without touching the engine.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from homeassistant.const import (
    ATTR_UNIT_OF_MEASUREMENT,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant

from ..const import (
    CONF_PV_FORECAST_POWER_ENTITY,
    CONF_PV_FORECAST_TODAY_ENTITY,
)
from ..data.models import Forecast


@runtime_checkable
class Forecaster(Protocol):
    """Produces a forward-looking forecast from the current state."""

    @property
    def entity_ids(self) -> list[str]:
        """Source entity ids to watch for changes (may be empty)."""

    def predict(self, hass: HomeAssistant) -> Forecast:
        """Return the latest forecast."""


def _numeric(hass: HomeAssistant, entity_id: str | None) -> tuple[float | None, str]:
    """Return an entity's numeric value and lowercased unit, or (None, '')."""
    if not entity_id:
        return None, ""
    state = hass.states.get(entity_id)
    if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN, ""):
        return None, ""
    try:
        value = float(state.state)
    except (ValueError, TypeError):
        return None, ""
    unit = str(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT, "")).lower()
    return value, unit


class NaiveForecaster:
    """A trivial forecaster that predicts nothing (the safe default)."""

    @property
    def entity_ids(self) -> list[str]:
        """Return no tracked entities."""
        return []

    def predict(self, hass: HomeAssistant) -> Forecast:
        """Return an empty forecast."""
        return Forecast()


class EntityForecaster:
    """Reads a PV forecast from configured Home Assistant entities."""

    def __init__(self, power_entity: str | None, today_entity: str | None) -> None:
        """Initialise with the forecast power and daily-energy entity ids."""
        self._power_entity = power_entity
        self._today_entity = today_entity

    @property
    def entity_ids(self) -> list[str]:
        """Return the configured forecast entities."""
        return [e for e in (self._power_entity, self._today_entity) if e]

    def predict(self, hass: HomeAssistant) -> Forecast:
        """Read the configured entities into a forecast."""
        power, power_unit = _numeric(hass, self._power_entity)
        if power is not None and power_unit in ("kw", "mw"):
            power *= 1000.0 if power_unit == "kw" else 1_000_000.0

        energy, energy_unit = _numeric(hass, self._today_entity)
        if energy is not None and energy_unit == "wh":
            energy /= 1000.0  # normalise to kWh

        return Forecast(pv_power_next_hour_w=power, pv_energy_today_kwh=energy)


def build_forecaster(options: dict[str, Any]) -> Forecaster:
    """Return an entity forecaster if configured, else the naive one."""
    power = options.get(CONF_PV_FORECAST_POWER_ENTITY)
    today = options.get(CONF_PV_FORECAST_TODAY_ENTITY)
    if power or today:
        return EntityForecaster(power, today)
    return NaiveForecaster()
