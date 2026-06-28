"""Tests for the KD Brain config and options flow."""

from __future__ import annotations

from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kd_brain.const import (
    CONF_SUPPLIER,
    CONF_SUPPLIER_MARKUP,
    CONF_VAT,
    DOMAIN,
)
from custom_components.kd_brain.data.providers import MANUAL, PROVIDERS

from .conftest import VALUES


async def test_user_flow_manual(hass: HomeAssistant, mock_epex) -> None:
    """Manual path: pick manual, then fill in values, and create an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_SUPPLIER: MANUAL}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "tariff"

    result = await hass.config_entries.flow.async_configure(result["flow_id"], VALUES)
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["options"][CONF_SUPPLIER] == MANUAL
    assert result["options"][CONF_VAT] == 0.21


async def test_user_flow_supplier_preset(hass: HomeAssistant, mock_epex) -> None:
    """Choosing a supplier pre-fills its markup on the tariff step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_SUPPLIER: "tibber"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "tariff"

    # The tariff form is pre-filled with Tibber's markup.
    defaults = result["data_schema"]({})
    assert defaults[CONF_SUPPLIER_MARKUP] == pytest.approx(
        float(PROVIDERS["tibber"].markup)
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"], VALUES)
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["options"][CONF_SUPPLIER] == "tibber"


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


async def test_options_flow_manual(
    hass: HomeAssistant, mock_entry: MockConfigEntry, mock_epex
) -> None:
    """Manual options path edits the stored values directly."""
    mock_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(mock_entry.entry_id)
    assert result["type"] is FlowResultType.MENU

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "manual"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "values"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {**VALUES, CONF_VAT: 0.09}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert mock_entry.options[CONF_VAT] == 0.09


async def test_options_flow_supplier_preset(
    hass: HomeAssistant, mock_entry: MockConfigEntry, mock_epex
) -> None:
    """Supplier options path pre-fills the chosen supplier's markup."""
    mock_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(mock_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "supplier"}
    )
    assert result["step_id"] == "supplier"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_SUPPLIER: "frank-energie"}
    )
    assert result["step_id"] == "values"
    defaults = result["data_schema"]({})
    assert defaults[CONF_SUPPLIER_MARKUP] == pytest.approx(
        float(PROVIDERS["frank-energie"].markup)
    )

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], VALUES
    )
    await hass.async_block_till_done()
    assert mock_entry.options[CONF_SUPPLIER] == "frank-energie"
