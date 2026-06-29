"""Integration tests for the actuation coordinator (observe vs active)."""

from __future__ import annotations

from freezegun import freeze_time
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_mock_service,
)

from custom_components.kd_brain.const import (
    CONF_BATTERY_POWER_CONTROL_ENTITY,
    CONF_CONTROL_MODE,
    CONF_GRID_POWER_ENTITY,
    CONTROL_ACTIVE,
    DOMAIN,
)

from .conftest import OPTIONS

FROZEN_TIME = "2026-06-28T08:30:00+00:00"
GRID = "sensor.kd_grid"
CONTROL = "number.kd_battery_power"


async def _state(hass: HomeAssistant, entry: MockConfigEntry, domain: str, key: str):
    ent_reg = er.async_get(hass)
    entity_id = ent_reg.async_get_entity_id(domain, DOMAIN, f"{entry.entry_id}_{key}")
    assert entity_id is not None
    return hass.states.get(entity_id)


async def test_observe_mode_does_not_write(hass: HomeAssistant, mock_epex) -> None:
    """In observe-only mode the safety-approved action is reported, not written."""
    calls = async_mock_service(hass, "number", "set_value")
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

        assert len(calls) == 0  # nothing written in observe mode

        last = await _state(hass, entry, "sensor", "last_actuation")
        assert last is not None
        assert last.state == "charge"  # gate approved a charge
        assert last.attributes["written"] is False

        active = await _state(hass, entry, "binary_sensor", "active_control")
        assert active is not None
        assert active.state == "off"


async def test_active_mode_writes_setpoint(hass: HomeAssistant, mock_epex) -> None:
    """In active mode a safety-approved charge is written to the control entity."""
    calls = async_mock_service(hass, "number", "set_value")
    await hass.config.async_set_time_zone("Europe/Amsterdam")
    with freeze_time(FROZEN_TIME):
        hass.states.async_set(GRID, "-2000", {"unit_of_measurement": "W"})
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="KD Brain",
            data={},
            options={
                **OPTIONS,
                CONF_GRID_POWER_ENTITY: GRID,
                CONF_CONTROL_MODE: CONTROL_ACTIVE,
                CONF_BATTERY_POWER_CONTROL_ENTITY: CONTROL,
            },
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert len(calls) == 1
        assert calls[0].data["entity_id"] == CONTROL
        assert calls[0].data["value"] == 2000.0  # surplus, within max charge power

        last = await _state(hass, entry, "sensor", "last_actuation")
        assert last is not None
        assert last.state == "charge"
        assert last.attributes["written"] is True

        active = await _state(hass, entry, "binary_sensor", "active_control")
        assert active is not None
        assert active.state == "on"
