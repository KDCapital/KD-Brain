"""Services for KD Brain."""

from __future__ import annotations

from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
    callback,
)
from homeassistant.exceptions import HomeAssistantError
import voluptuous as vol

from .const import DOMAIN
from .dashboards import build_dashboard

SERVICE_RECALCULATE = "recalculate"
SERVICE_GENERATE_DASHBOARD = "generate_dashboard"

_GENERATE_DASHBOARD_SCHEMA = vol.Schema({vol.Optional("entry_id"): str})


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Register KD Brain services (idempotent)."""
    if hass.services.has_service(DOMAIN, SERVICE_RECALCULATE):
        return

    async def _async_recalculate(call: ServiceCall) -> None:
        """Force every loaded KD Brain entry to refresh its prices."""
        for entry in hass.config_entries.async_loaded_entries(DOMAIN):
            await entry.runtime_data.price_coordinator.async_request_refresh()

    async def _async_generate_dashboard(call: ServiceCall) -> ServiceResponse:
        """Build an auto-generated dashboard for a (or the only) config entry."""
        entry_id = call.data.get("entry_id")
        if entry_id is None:
            loaded = hass.config_entries.async_loaded_entries(DOMAIN)
            if not loaded:
                raise HomeAssistantError("No loaded KD Brain config entry found")
            entry_id = loaded[0].entry_id
        return {"dashboard": build_dashboard(hass, entry_id)}

    hass.services.async_register(DOMAIN, SERVICE_RECALCULATE, _async_recalculate)
    hass.services.async_register(
        DOMAIN,
        SERVICE_GENERATE_DASHBOARD,
        _async_generate_dashboard,
        schema=_GENERATE_DASHBOARD_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )


@callback
def async_unload_services(hass: HomeAssistant) -> None:
    """Remove KD Brain services when no entries remain."""
    if not hass.config_entries.async_loaded_entries(DOMAIN):
        hass.services.async_remove(DOMAIN, SERVICE_RECALCULATE)
        hass.services.async_remove(DOMAIN, SERVICE_GENERATE_DASHBOARD)
