"""Tests for the telemetry entity adapter."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from custom_components.kd_brain.const import (
    CONF_BATTERY_CAPACITY_WH,
    CONF_BATTERY_POWER_ENTITIES,
    CONF_BATTERY_SOC_ENTITIES,
    CONF_GRID_POWER_ENTITY,
    CONF_IMBALANCE_PRICE_ENTITY,
    CONF_IMBALANCE_UNIT,
    CONF_PV_POWER_ENTITY,
    IMBALANCE_UNIT_MWH,
)
from custom_components.kd_brain.data.adapters.entity_adapter import EntityAdapter


async def test_reads_states_with_unit_conversion(hass: HomeAssistant) -> None:
    """The adapter reads states and converts kW to W."""
    hass.states.async_set("sensor.grid", "1500", {"unit_of_measurement": "W"})
    hass.states.async_set("sensor.pv", "2", {"unit_of_measurement": "kW"})
    hass.states.async_set("sensor.soc", "55", {"unit_of_measurement": "%"})
    hass.states.async_set("sensor.bp", "-500", {"unit_of_measurement": "W"})

    adapter = EntityAdapter(
        {
            CONF_GRID_POWER_ENTITY: "sensor.grid",
            CONF_PV_POWER_ENTITY: "sensor.pv",
            CONF_BATTERY_SOC_ENTITIES: ["sensor.soc"],
            CONF_BATTERY_POWER_ENTITIES: ["sensor.bp"],
            CONF_BATTERY_CAPACITY_WH: 5000,
        }
    )
    telemetry = adapter.read(hass)

    assert telemetry.grid.power_w == 1500.0
    assert telemetry.pv.power_w == 2000.0  # 2 kW -> 2000 W
    assert telemetry.batteries[0].soc == 55.0
    assert telemetry.batteries[0].power_w == -500.0
    assert telemetry.batteries[0].capacity_wh == 5000


async def test_handles_unavailable_and_missing(hass: HomeAssistant) -> None:
    """Unavailable, unknown or missing entities yield None."""
    hass.states.async_set("sensor.grid", "unavailable")
    adapter = EntityAdapter(
        {CONF_GRID_POWER_ENTITY: "sensor.grid", CONF_PV_POWER_ENTITY: "sensor.gone"}
    )
    telemetry = adapter.read(hass)
    assert telemetry.grid.power_w is None
    assert telemetry.pv.power_w is None


async def test_multiple_batteries(hass: HomeAssistant) -> None:
    """One battery state is built per configured SOC entity."""
    hass.states.async_set("sensor.s1", "40", {"unit_of_measurement": "%"})
    hass.states.async_set("sensor.s2", "60", {"unit_of_measurement": "%"})
    adapter = EntityAdapter(
        {
            CONF_BATTERY_SOC_ENTITIES: ["sensor.s1", "sensor.s2"],
            CONF_BATTERY_CAPACITY_WH: 5000,
        }
    )
    telemetry = adapter.read(hass)
    assert len(telemetry.batteries) == 2
    assert telemetry.battery_soc_average() == 50.0


def test_entity_ids_and_is_configured() -> None:
    """The adapter reports its tracked entities and configured state."""
    adapter = EntityAdapter(
        {
            CONF_GRID_POWER_ENTITY: "sensor.grid",
            CONF_BATTERY_SOC_ENTITIES: ["sensor.a", "sensor.b"],
            CONF_IMBALANCE_PRICE_ENTITY: "sensor.imbalance",
        }
    )
    assert set(adapter.entity_ids) == {
        "sensor.grid",
        "sensor.a",
        "sensor.b",
        "sensor.imbalance",
    }
    assert adapter.is_configured
    assert not EntityAdapter({}).is_configured


async def test_imbalance_price_kwh(hass: HomeAssistant) -> None:
    """An imbalance price already in €/kWh is read as-is (and may be negative)."""
    hass.states.async_set("sensor.imb", "-0.05", {"unit_of_measurement": "€/kWh"})
    adapter = EntityAdapter({CONF_IMBALANCE_PRICE_ENTITY: "sensor.imb"})
    assert adapter.read(hass).imbalance_price == -0.05


async def test_imbalance_price_mwh_conversion(hass: HomeAssistant) -> None:
    """An imbalance price in €/MWh is converted to €/kWh."""
    hass.states.async_set("sensor.imb", "120", {"unit_of_measurement": "€/MWh"})
    adapter = EntityAdapter(
        {
            CONF_IMBALANCE_PRICE_ENTITY: "sensor.imb",
            CONF_IMBALANCE_UNIT: IMBALANCE_UNIT_MWH,
        }
    )
    assert adapter.read(hass).imbalance_price == 0.12  # 120 €/MWh -> 0.12 €/kWh
