"""Custom sidebar panel registration for KD Brain.

KD Brain ships a self-contained frontend web component (vanilla JS, no build
step) served as a static asset and registered as a Home Assistant sidebar
panel. The panel reads live state from the injected ``hass`` object and talks to
the integration's own websocket API for the consolidated snapshot and for
reading/writing configuration.
"""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import DOMAIN, INTEGRATION_VERSION

_LOGGER = logging.getLogger(__name__)

PANEL_URL_PATH = "kd-brain"
PANEL_TITLE = "KD Brain"
PANEL_ICON = "mdi:home-lightning-bolt"
PANEL_WEBCOMPONENT = "kd-brain-panel"

STATIC_URL = "/kd_brain_static"
FRONTEND_DIR = Path(__file__).parent / "frontend"
MODULE_URL = f"{STATIC_URL}/kd-brain-panel.js?v={INTEGRATION_VERSION}"

# hass.data flags so the shared static path and panel register only once, even
# though setup runs per config entry (there is only ever one, but be safe).
_STATIC_KEY = f"{DOMAIN}_static_registered"
_PANEL_KEY = f"{DOMAIN}_panel_registered"


async def async_register_frontend(hass: HomeAssistant) -> None:
    """Serve the frontend assets and register the sidebar panel (idempotent).

    The panel only makes sense when the ``frontend`` integration is available;
    it always is on a real Home Assistant install. When it is not (e.g. a
    minimal test harness without the compiled frontend), registration is skipped
    so the rest of the integration still loads normally.
    """
    if "frontend" not in hass.config.components:
        _LOGGER.debug("frontend not available; skipping KD Brain panel")
        return

    if not hass.data.get(_STATIC_KEY):
        await hass.http.async_register_static_paths(
            [StaticPathConfig(STATIC_URL, str(FRONTEND_DIR), cache_headers=False)]
        )
        hass.data[_STATIC_KEY] = True

    if hass.data.get(_PANEL_KEY):
        return

    await panel_custom.async_register_panel(
        hass,
        frontend_url_path=PANEL_URL_PATH,
        webcomponent_name=PANEL_WEBCOMPONENT,
        module_url=MODULE_URL,
        sidebar_title=PANEL_TITLE,
        sidebar_icon=PANEL_ICON,
        require_admin=False,
        config={},
    )
    hass.data[_PANEL_KEY] = True


def async_unregister_frontend(hass: HomeAssistant) -> None:
    """Remove the sidebar panel on unload (static path stays for the HA run)."""
    if hass.data.pop(_PANEL_KEY, False):
        frontend.async_remove_panel(hass, PANEL_URL_PATH)
