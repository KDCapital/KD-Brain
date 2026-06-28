"""Services for KD Brain."""

from __future__ import annotations

from homeassistant.core import HomeAssistant, ServiceCall, callback

from .const import DOMAIN

SERVICE_RECALCULATE = "recalculate"


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Register KD Brain services (idempotent)."""
    if hass.services.has_service(DOMAIN, SERVICE_RECALCULATE):
        return

    async def _async_recalculate(call: ServiceCall) -> None:
        """Force every loaded KD Brain entry to refresh its prices."""
        for entry in hass.config_entries.async_loaded_entries(DOMAIN):
            await entry.runtime_data.price_coordinator.async_request_refresh()

    hass.services.async_register(DOMAIN, SERVICE_RECALCULATE, _async_recalculate)


@callback
def async_unload_services(hass: HomeAssistant) -> None:
    """Remove KD Brain services when no entries remain."""
    if not hass.config_entries.async_loaded_entries(DOMAIN):
        hass.services.async_remove(DOMAIN, SERVICE_RECALCULATE)
