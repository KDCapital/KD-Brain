"""Tests for the forecasting interface and the forecast sensor."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kd_brain.const import (
    CONF_PV_FORECAST_POWER_ENTITY,
    DOMAIN,
)
from custom_components.kd_brain.engine.forecaster import (
    EntityForecaster,
    NaiveForecaster,
    build_forecaster,
)

from .conftest import OPTIONS


async def test_entity_forecaster_reads_and_converts(hass: HomeAssistant) -> None:
    hass.states.async_set("sensor.pvf", "1.5", {"unit_of_measurement": "kW"})
    hass.states.async_set("sensor.pvt", "12", {"unit_of_measurement": "kWh"})
    forecaster = EntityForecaster("sensor.pvf", "sensor.pvt")

    forecast = forecaster.predict(hass)

    assert forecast.pv_power_next_hour_w == 1500.0  # kW -> W
    assert forecast.pv_energy_today_kwh == 12.0
    assert set(forecaster.entity_ids) == {"sensor.pvf", "sensor.pvt"}


async def test_entity_forecaster_wh_to_kwh(hass: HomeAssistant) -> None:
    hass.states.async_set("sensor.pvt", "8000", {"unit_of_measurement": "Wh"})
    forecaster = EntityForecaster(None, "sensor.pvt")
    assert forecaster.predict(hass).pv_energy_today_kwh == 8.0


async def test_naive_forecaster(hass: HomeAssistant) -> None:
    forecaster = NaiveForecaster()
    assert forecaster.entity_ids == []
    forecast = forecaster.predict(hass)
    assert forecast.pv_power_next_hour_w is None
    assert forecast.pv_energy_today_kwh is None


def test_build_forecaster_selects_type() -> None:
    assert isinstance(build_forecaster({}), NaiveForecaster)
    assert isinstance(
        build_forecaster({CONF_PV_FORECAST_POWER_ENTITY: "sensor.x"}),
        EntityForecaster,
    )


async def test_forecast_sensor(hass: HomeAssistant, mock_epex) -> None:
    """The forecast power sensor reflects the configured entity."""
    hass.states.async_set("sensor.kd_pvf", "2.0", {"unit_of_measurement": "kW"})
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="KD Brain",
        data={},
        options={**OPTIONS, CONF_PV_FORECAST_POWER_ENTITY: "sensor.kd_pvf"},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    ent_reg = er.async_get(hass)
    entity_id = ent_reg.async_get_entity_id(
        "sensor", DOMAIN, f"{entry.entry_id}_pv_forecast_power"
    )
    assert entity_id is not None
    assert float(hass.states.get(entity_id).state) == 2000.0  # type: ignore[union-attr]
