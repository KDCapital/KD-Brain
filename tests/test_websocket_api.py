"""Tests for the KD Brain websocket API (snapshot + config get/update)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kd_brain.const import CONF_VAT


async def _setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def test_snapshot_command(
    hass: HomeAssistant,
    mock_entry: MockConfigEntry,
    mock_epex: Any,
    hass_ws_client: Callable[..., Any],
) -> None:
    """The snapshot command returns prices and the live sections."""
    await _setup(hass, mock_entry)
    client = await hass_ws_client(hass)

    await client.send_json_auto_id({"type": "kd_brain/snapshot"})
    msg = await client.receive_json()

    assert msg["success"]
    result = msg["result"]
    assert result["prices"]["available"] is True
    assert "today" in result["prices"]
    assert "active_control" in result
    assert "forecast" in result


async def test_config_get_command(
    hass: HomeAssistant,
    mock_entry: MockConfigEntry,
    mock_epex: Any,
    hass_ws_client: Callable[..., Any],
) -> None:
    """config/get returns the options plus provider presets and enums."""
    await _setup(hass, mock_entry)
    client = await hass_ws_client(hass)

    await client.send_json_auto_id({"type": "kd_brain/config/get"})
    msg = await client.receive_json()

    assert msg["success"]
    result = msg["result"]
    assert CONF_VAT in result["options"]
    assert any(p["id"] == "tibber" for p in result["providers"])
    assert "control_mode" in result["enums"]


async def test_config_update_persists_and_reloads(
    hass: HomeAssistant,
    mock_entry: MockConfigEntry,
    mock_epex: Any,
    hass_ws_client: Callable[..., Any],
) -> None:
    """config/update writes allowed keys into the entry options."""
    await _setup(hass, mock_entry)
    client = await hass_ws_client(hass)

    await client.send_json_auto_id(
        {"type": "kd_brain/config/update", "changes": {CONF_VAT: 0.09}}
    )
    msg = await client.receive_json()
    await hass.async_block_till_done()

    assert msg["success"]
    assert mock_entry.options[CONF_VAT] == 0.09


async def test_config_update_rejects_unknown_keys(
    hass: HomeAssistant,
    mock_entry: MockConfigEntry,
    mock_epex: Any,
    hass_ws_client: Callable[..., Any],
) -> None:
    """config/update refuses keys outside the editable allowlist."""
    await _setup(hass, mock_entry)
    client = await hass_ws_client(hass)

    await client.send_json_auto_id(
        {"type": "kd_brain/config/update", "changes": {"evil_key": 1}}
    )
    msg = await client.receive_json()

    assert not msg["success"]
    assert msg["error"]["code"] == "invalid_keys"
