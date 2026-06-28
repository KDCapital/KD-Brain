"""Tests for KD Brain price entities."""

from __future__ import annotations

from freezegun import freeze_time
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kd_brain.const import DOMAIN

# 10:30 local time (Europe/Amsterdam, +02:00) on the fixture's "today".
FROZEN_TIME = "2026-06-28T08:30:00+00:00"


async def _setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def test_price_sensors(
    hass: HomeAssistant, mock_entry: MockConfigEntry, mock_epex
) -> None:
    """Price sensors expose the expected all-in and market values."""
    await hass.config.async_set_time_zone("Europe/Amsterdam")
    with freeze_time(FROZEN_TIME):
        await _setup(hass, mock_entry)

        ent_reg = er.async_get(hass)

        def value(domain: str, key: str) -> str:
            entity_id = ent_reg.async_get_entity_id(
                domain, DOMAIN, f"{mock_entry.entry_id}_{key}"
            )
            assert entity_id is not None
            state = hass.states.get(entity_id)
            assert state is not None
            return state.state

        assert float(value("sensor", "current_price")) == pytest.approx(0.3146)
        assert float(value("sensor", "current_market_price")) == pytest.approx(0.14)
        assert float(value("sensor", "current_feed_in_price")) == pytest.approx(0.1694)
        assert float(value("sensor", "next_price")) == pytest.approx(0.3388)
        assert float(value("sensor", "min_price_today")) == pytest.approx(0.2662)
        assert float(value("sensor", "max_price_today")) == pytest.approx(0.4598)
        assert float(value("sensor", "average_price_today")) == pytest.approx(0.363)

        assert value("binary_sensor", "price_low") == "off"

        data_entity = ent_reg.async_get_entity_id(
            "sensor", DOMAIN, f"{mock_entry.entry_id}_price_data"
        )
        assert data_entity is not None
        attrs = hass.states.get(data_entity).attributes  # type: ignore[union-attr]
        assert len(attrs["today"]) == 8
        assert len(attrs["tomorrow"]) == 4
