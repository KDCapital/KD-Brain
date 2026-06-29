"""Integration tests for telemetry sensors and push updates."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kd_brain.const import (
    CONF_BATTERY_CAPACITY_WH,
    CONF_BATTERY_POWER_ENTITIES,
    CONF_BATTERY_SOC_ENTITIES,
    CONF_GRID_POWER_ENTITY,
    CONF_IMBALANCE_PRICE_ENTITY,
    CONF_PV_POWER_ENTITY,
    DOMAIN,
)

from .conftest import OPTIONS

GRID = "sensor.kd_grid"
PV = "sensor.kd_pv"
SOC = "sensor.kd_soc"
BPOWER = "sensor.kd_battery_power"


async def test_telemetry_sensors_and_push_update(
    hass: HomeAssistant, mock_epex
) -> None:
    """Telemetry sensors report adapter values and update on source changes."""
    hass.states.async_set(GRID, "1500", {"unit_of_measurement": "W"})
    hass.states.async_set(PV, "2", {"unit_of_measurement": "kW"})
    hass.states.async_set(SOC, "55", {"unit_of_measurement": "%"})
    hass.states.async_set(BPOWER, "-500", {"unit_of_measurement": "W"})

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="KD Brain",
        data={},
        options={
            **OPTIONS,
            CONF_GRID_POWER_ENTITY: GRID,
            CONF_PV_POWER_ENTITY: PV,
            CONF_BATTERY_SOC_ENTITIES: [SOC],
            CONF_BATTERY_POWER_ENTITIES: [BPOWER],
            CONF_BATTERY_CAPACITY_WH: 5000,
        },
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    ent_reg = er.async_get(hass)

    def value(key: str) -> str:
        entity_id = ent_reg.async_get_entity_id(
            "sensor", DOMAIN, f"{entry.entry_id}_{key}"
        )
        assert entity_id is not None
        state = hass.states.get(entity_id)
        assert state is not None
        return state.state

    assert float(value("grid_power")) == 1500.0
    assert float(value("pv_power")) == 2000.0  # kW -> W
    assert float(value("battery_soc")) == 55.0
    assert float(value("battery_power")) == -500.0
    # derived load = pv + grid - battery = 2000 + 1500 - (-500)
    assert float(value("load_power")) == 4000.0

    # A source change pushes a telemetry refresh.
    hass.states.async_set(GRID, "2500", {"unit_of_measurement": "W"})
    await hass.async_block_till_done()
    assert float(value("grid_power")) == 2500.0


async def test_no_telemetry_sensors_when_unconfigured(
    hass: HomeAssistant, mock_entry: MockConfigEntry, mock_epex
) -> None:
    """Without configured devices, no telemetry sensors are created."""
    mock_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_entry.entry_id)
    await hass.async_block_till_done()

    ent_reg = er.async_get(hass)
    assert (
        ent_reg.async_get_entity_id(
            "sensor", DOMAIN, f"{mock_entry.entry_id}_grid_power"
        )
        is None
    )


async def test_imbalance_price_sensor(hass: HomeAssistant, mock_epex) -> None:
    """The imbalance price sensor reports the configured entity's value."""
    hass.states.async_set(
        "sensor.kd_imbalance", "0.18", {"unit_of_measurement": "€/kWh"}
    )
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="KD Brain",
        data={},
        options={**OPTIONS, CONF_IMBALANCE_PRICE_ENTITY: "sensor.kd_imbalance"},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    ent_reg = er.async_get(hass)
    entity_id = ent_reg.async_get_entity_id(
        "sensor", DOMAIN, f"{entry.entry_id}_imbalance_price"
    )
    assert entity_id is not None
    assert float(hass.states.get(entity_id).state) == 0.18  # type: ignore[union-attr]
