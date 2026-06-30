"""Read telemetry from configured Home Assistant entities.

KD Brain is an orchestration layer: instead of duplicating device integrations
it reads the entities those integrations already provide (HomeWizard P1,
Growatt, Marstek, ...). The :class:`EntityAdapter` maps configured entity ids
onto an immutable :class:`Telemetry` snapshot.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from homeassistant.const import (
    ATTR_UNIT_OF_MEASUREMENT,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant

from ...const import (
    CONF_BATTERY_CAPACITY_WH,
    CONF_BATTERY_POWER_ENTITIES,
    CONF_BATTERY_SOC_ENTITIES,
    CONF_EV_CONNECTED_ENTITY,
    CONF_EV_POWER_ENTITY,
    CONF_EV_SOC_ENTITY,
    CONF_GRID_POWER_ENTITY,
    CONF_IMBALANCE_PRICE_ENTITY,
    CONF_IMBALANCE_UNIT,
    CONF_LOAD_POWER_ENTITY,
    CONF_PV_POWER_ENTITY,
    DEFAULT_BATTERY_CAPACITY_WH,
    DEFAULT_IMBALANCE_UNIT,
    IMBALANCE_UNIT_MWH,
)
from ..models import (
    BatteryState,
    EvState,
    GridState,
    LoadState,
    PvState,
    Telemetry,
)

_TRUE_STATES = frozenset({"on", "true", "1", "home", "connected", "charging"})
_FALSE_STATES = frozenset({"off", "false", "0", "not_connected", "disconnected"})

_POWER_TO_WATT: dict[str, float] = {"w": 1.0, "kw": 1000.0, "mw": 1_000_000.0}


def _as_list(value: Any) -> list[str]:
    """Coerce an option value into a list of entity ids."""
    if not value:
        return []
    if isinstance(value, str):
        return [value]
    return list(value)


class EntityAdapter:
    """Builds telemetry snapshots from configured source entities."""

    def __init__(self, options: Mapping[str, Any]) -> None:
        """Initialise the adapter from config entry options."""
        self._grid = options.get(CONF_GRID_POWER_ENTITY)
        self._pv = options.get(CONF_PV_POWER_ENTITY)
        self._load = options.get(CONF_LOAD_POWER_ENTITY)
        self._soc = _as_list(options.get(CONF_BATTERY_SOC_ENTITIES))
        self._power = _as_list(options.get(CONF_BATTERY_POWER_ENTITIES))
        self._capacity = int(
            options.get(CONF_BATTERY_CAPACITY_WH) or DEFAULT_BATTERY_CAPACITY_WH
        )
        self._imbalance = options.get(CONF_IMBALANCE_PRICE_ENTITY)
        self._imbalance_unit = (
            options.get(CONF_IMBALANCE_UNIT) or DEFAULT_IMBALANCE_UNIT
        )
        self._ev_connected = options.get(CONF_EV_CONNECTED_ENTITY)
        self._ev_power = options.get(CONF_EV_POWER_ENTITY)
        self._ev_soc = options.get(CONF_EV_SOC_ENTITY)

    @property
    def entity_ids(self) -> list[str]:
        """Return every source entity id, for state-change tracking."""
        ids = [
            self._grid,
            self._pv,
            self._load,
            self._imbalance,
            self._ev_connected,
            self._ev_power,
            self._ev_soc,
            *self._soc,
            *self._power,
        ]
        return [entity_id for entity_id in ids if entity_id]

    @property
    def is_configured(self) -> bool:
        """Return whether any telemetry source is configured."""
        return bool(self.entity_ids)

    def read(self, hass: HomeAssistant) -> Telemetry:
        """Read current states and build an immutable telemetry snapshot."""
        return Telemetry(
            grid=GridState(power_w=self._power_w(hass, self._grid)),
            pv=PvState(power_w=self._power_w(hass, self._pv)),
            batteries=self._batteries(hass),
            load=LoadState(power_w=self._power_w(hass, self._load)),
            ev=EvState(
                connected=self._bool(hass, self._ev_connected),
                charging_power_w=self._power_w(hass, self._ev_power),
                soc=self._numeric(hass, self._ev_soc),
            ),
            imbalance_price=self._imbalance_price(hass),
        )

    @staticmethod
    def _bool(hass: HomeAssistant, entity_id: str | None) -> bool | None:
        """Return a boolean state, or None if unknown/unset."""
        if not entity_id:
            return None
        state = hass.states.get(entity_id)
        if state is None:
            return None
        value = state.state.lower()
        if value in _TRUE_STATES:
            return True
        if value in _FALSE_STATES:
            return False
        return None

    def _imbalance_price(self, hass: HomeAssistant) -> float | None:
        """Return the imbalance price in €/kWh, converting from €/MWh if set."""
        value = self._numeric(hass, self._imbalance)
        if value is None:
            return None
        if self._imbalance_unit == IMBALANCE_UNIT_MWH:
            return value / 1000.0
        return value

    def _batteries(self, hass: HomeAssistant) -> tuple[BatteryState, ...]:
        """Build one battery state per configured SOC/power entity."""
        count = max(len(self._soc), len(self._power))
        batteries: list[BatteryState] = []
        for index in range(count):
            soc_id = self._soc[index] if index < len(self._soc) else None
            power_id = self._power[index] if index < len(self._power) else None
            batteries.append(
                BatteryState(
                    soc=self._numeric(hass, soc_id),
                    power_w=self._power_w(hass, power_id),
                    capacity_wh=self._capacity,
                )
            )
        return tuple(batteries)

    @staticmethod
    def _numeric(hass: HomeAssistant, entity_id: str | None) -> float | None:
        """Return the numeric state of an entity, or None if unusable."""
        if not entity_id:
            return None
        state = hass.states.get(entity_id)
        if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN, ""):
            return None
        try:
            return float(state.state)
        except (ValueError, TypeError):
            return None

    @classmethod
    def _power_w(cls, hass: HomeAssistant, entity_id: str | None) -> float | None:
        """Return an entity's power in watts, converting kW/MW if needed."""
        value = cls._numeric(hass, entity_id)
        if value is None or not entity_id:
            return None
        state = hass.states.get(entity_id)
        unit = ""
        if state is not None:
            unit = str(state.attributes.get(ATTR_UNIT_OF_MEASUREMENT, "")).lower()
        return value * _POWER_TO_WATT.get(unit, 1.0)
