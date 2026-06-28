"""Integration tests for the optimisation coordinator and its sensors."""

from __future__ import annotations

from freezegun import freeze_time
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kd_brain.const import CONF_GRID_POWER_ENTITY, DOMAIN

from .conftest import OPTIONS

# 10:30 local (Europe/Amsterdam) -> within the fixture's price day.
FROZEN_TIME = "2026-06-28T08:30:00+00:00"
GRID = "sensor.kd_grid"


async def test_recommended_action_reflects_self_consumption(
    hass: HomeAssistant, mock_epex
) -> None:
    """A solar surplus drives a CHARGE recommendation from self-consumption."""
    await hass.config.async_set_time_zone("Europe/Amsterdam")
    with freeze_time(FROZEN_TIME):
        hass.states.async_set(GRID, "-2000", {"unit_of_measurement": "W"})
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="KD Brain",
            data={},
            options={**OPTIONS, CONF_GRID_POWER_ENTITY: GRID},
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        ent_reg = er.async_get(hass)

        def state(key: str):
            entity_id = ent_reg.async_get_entity_id(
                "sensor", DOMAIN, f"{entry.entry_id}_{key}"
            )
            assert entity_id is not None
            return hass.states.get(entity_id)

        action = state("recommended_action")
        assert action is not None
        assert action.state == "charge"
        assert "considered" in action.attributes
        assert action.attributes["why"]

        strategy = state("active_strategy")
        assert strategy is not None
        assert strategy.state == "self_consumption"


async def test_recommended_action_idle_without_data(
    hass: HomeAssistant, mock_entry: MockConfigEntry, mock_epex
) -> None:
    """Outside the price horizon and without telemetry the engine idles."""
    with freeze_time("2020-01-01T00:00:00+00:00"):
        mock_entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(mock_entry.entry_id)
        await hass.async_block_till_done()

        ent_reg = er.async_get(hass)
        entity_id = ent_reg.async_get_entity_id(
            "sensor", DOMAIN, f"{mock_entry.entry_id}_recommended_action"
        )
        assert entity_id is not None
        assert hass.states.get(entity_id).state == "idle"  # type: ignore[union-attr]
