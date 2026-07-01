"""An actuator that writes a heat pump setpoint offset to a number entity."""

from __future__ import annotations

import logging

from homeassistant.components.number import DOMAIN as NUMBER_DOMAIN
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

_SERVICE_SET_VALUE = "set_value"
_ATTR_VALUE = "value"


class HeatPumpActuator:
    """Writes a °C setpoint offset to a number entity.

    The target entity is a "heating curve offset" number provided by the user's
    heat pump integration, so KD Brain never writes raw registers itself.
    """

    def __init__(self, entity_id: str) -> None:
        """Initialise with the control entity id."""
        self._entity_id = entity_id

    @property
    def name(self) -> str:
        """Return the actuator identifier."""
        return "heatpump"

    @property
    def is_configured(self) -> bool:
        """Return whether a control entity is set."""
        return bool(self._entity_id)

    async def async_apply(self, hass: HomeAssistant, offset_c: float) -> None:
        """Set the control entity to the given offset in °C."""
        _LOGGER.debug("Setting %s to %.1f °C", self._entity_id, offset_c)
        await hass.services.async_call(
            NUMBER_DOMAIN,
            _SERVICE_SET_VALUE,
            {ATTR_ENTITY_ID: self._entity_id, _ATTR_VALUE: float(offset_c)},
            blocking=True,
        )
