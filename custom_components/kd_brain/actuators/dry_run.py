"""A no-op actuator used in observe-only mode and as a safe fallback."""

from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class DryRunActuator:
    """Logs what would happen but never writes to a device."""

    @property
    def name(self) -> str:
        """Return the actuator identifier."""
        return "dry_run"

    @property
    def is_configured(self) -> bool:
        """A dry-run actuator has no real control path, so it never writes."""
        return False

    async def async_apply(self, hass: HomeAssistant, signed_w: int) -> None:
        """Record the intended write without performing it."""
        _LOGGER.debug("Dry-run: would set battery power to %d W", signed_w)
