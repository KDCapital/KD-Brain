"""Tests for the custom sidebar panel registration."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import HomeAssistant

from custom_components.kd_brain import panel as panel_mod


async def test_register_and_unregister_panel(hass: HomeAssistant) -> None:
    """The panel is registered once and removed on unregister."""
    hass.config.components.add("frontend")
    hass.http = MagicMock()
    hass.http.async_register_static_paths = AsyncMock()

    with (
        patch.object(
            panel_mod.panel_custom, "async_register_panel", AsyncMock()
        ) as register,
        patch.object(panel_mod.frontend, "async_remove_panel") as remove,
    ):
        await panel_mod.async_register_frontend(hass)
        register.assert_awaited_once()
        hass.http.async_register_static_paths.assert_awaited_once()
        assert hass.data[panel_mod._PANEL_KEY] is True

        # Idempotent: a second call does not register again.
        await panel_mod.async_register_frontend(hass)
        register.assert_awaited_once()

        panel_mod.async_unregister_frontend(hass)
        remove.assert_called_once_with(hass, panel_mod.PANEL_URL_PATH)
        assert panel_mod._PANEL_KEY not in hass.data


async def test_register_skipped_without_frontend(hass: HomeAssistant) -> None:
    """Without the frontend integration the panel is skipped, not an error."""
    assert "frontend" not in hass.config.components
    with patch.object(
        panel_mod.panel_custom, "async_register_panel", AsyncMock()
    ) as register:
        await panel_mod.async_register_frontend(hass)
        register.assert_not_awaited()
        assert panel_mod._PANEL_KEY not in hass.data
