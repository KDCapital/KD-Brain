"""Tests for setup, unload and repair issues."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.kd_brain.const import DOMAIN, ISSUE_PRICE_SOURCE_UNAVAILABLE
from custom_components.kd_brain.data.sources.epexprijzen import API_URL
from custom_components.kd_brain.services import (
    SERVICE_GENERATE_DASHBOARD,
    SERVICE_RECALCULATE,
)


async def test_setup_and_unload(
    hass: HomeAssistant, mock_entry: MockConfigEntry, mock_epex
) -> None:
    """A config entry loads its coordinator and unloads cleanly."""
    mock_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_entry.state is ConfigEntryState.LOADED
    coordinator = mock_entry.runtime_data.price_coordinator
    assert coordinator.data is not None
    assert len(coordinator.data.points) == 12
    assert hass.services.has_service(DOMAIN, SERVICE_RECALCULATE)

    assert await hass.config_entries.async_unload(mock_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_entry.state is ConfigEntryState.NOT_LOADED


async def test_recalculate_service_refreshes(
    hass: HomeAssistant, mock_entry: MockConfigEntry, mock_epex: AiohttpClientMocker
) -> None:
    """The recalculate service triggers a new fetch."""
    mock_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    calls_before = len(mock_epex.mock_calls)
    await hass.services.async_call(DOMAIN, SERVICE_RECALCULATE, blocking=True)
    await hass.async_block_till_done()
    assert len(mock_epex.mock_calls) > calls_before


async def test_generate_dashboard_service_returns_cards(
    hass: HomeAssistant, mock_entry: MockConfigEntry, mock_epex: AiohttpClientMocker
) -> None:
    """The dashboard service returns a Lovelace config built from real entities."""
    mock_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    response = await hass.services.async_call(
        DOMAIN,
        SERVICE_GENERATE_DASHBOARD,
        {"entry_id": mock_entry.entry_id},
        blocking=True,
        return_response=True,
    )
    assert response is not None
    dashboard = response["dashboard"]
    cards = dashboard["views"][0]["cards"]
    assert any(card["title"] == "Prijzen" for card in cards)
    price_card = next(card for card in cards if card["title"] == "Prijzen")
    assert "sensor.kd_brain_current_price" in price_card["entities"]
    assert "binary_sensor.kd_brain_price_is_low" in price_card["entities"]


async def test_setup_failure_creates_repair_issue(
    hass: HomeAssistant,
    mock_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """A failing price source raises a repair issue and retries setup."""
    aioclient_mock.get(API_URL, status=500)
    mock_entry.add_to_hass(hass)
    assert not await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_entry.state is ConfigEntryState.SETUP_RETRY
    issue_registry = ir.async_get(hass)
    issue = issue_registry.async_get_issue(DOMAIN, ISSUE_PRICE_SOURCE_UNAVAILABLE)
    assert issue is not None
