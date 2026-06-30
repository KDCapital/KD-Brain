"""An actuator that drives a Home Assistant ``number`` control entity."""

from __future__ import annotations

import logging

from homeassistant.components.number import DOMAIN as NUMBER_DOMAIN
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

# number.set_value service contract (kept as literals to avoid relying on
# non-exported component constants).
_SERVICE_SET_VALUE = "set_value"
_ATTR_VALUE = "value"


class EntityActuator:
    """Writes a signed battery power setpoint to a number entity.

    Positive values charge, negative values discharge, zero is idle. The target
    entity is provided by the user's battery integration (e.g. a "force charge
    power" number), so KD Brain never writes raw registers itself.
    """

    def __init__(self, entity_id: str) -> None:
        """Initialise with the control entity id."""
        self._entity_id = entity_id

    @property
    def name(self) -> str:
        """Return the actuator identifier."""
        return "entity"

    @property
    def is_configured(self) -> bool:
        """Return whether a control entity is set."""
        return bool(self._entity_id)

    async def async_apply(self, hass: HomeAssistant, signed_w: int) -> None:
        """Set the control entity to the given value (watts or amps)."""
        _LOGGER.debug("Setting %s to %d", self._entity_id, signed_w)
        await hass.services.async_call(
            NUMBER_DOMAIN,
            _SERVICE_SET_VALUE,
            {ATTR_ENTITY_ID: self._entity_id, _ATTR_VALUE: float(signed_w)},
            blocking=True,
        )
