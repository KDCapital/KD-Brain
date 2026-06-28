"""Tests for the KD Brain config and options flow."""

from __future__ import annotations

from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kd_brain.const import CONF_VAT, DOMAIN

from .conftest import OPTIONS


async def test_user_flow_creates_entry(hass: HomeAssistant, mock_epex) -> None:
    """The user flow creates an entry storing the tariff options."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(result["flow_id"], OPTIONS)
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "KD Brain"
    assert result["options"][CONF_VAT] == 0.21


async def test_single_instance_allowed(
    hass: HomeAssistant, mock_entry: MockConfigEntry
) -> None:
    """A second instance is rejected."""
    mock_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"


async def test_options_flow_updates_options(
    hass: HomeAssistant, mock_entry: MockConfigEntry, mock_epex
) -> None:
    """The options flow updates the stored tariff configuration."""
    mock_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(mock_entry.entry_id)
    assert result["type"] is FlowResultType.FORM

    new_options = {**OPTIONS, CONF_VAT: 0.09}
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], new_options
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert mock_entry.options[CONF_VAT] == 0.09
