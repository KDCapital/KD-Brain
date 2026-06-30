"""Tests for EV smart charging (planner, IEC safety, integration)."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from freezegun import freeze_time
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_mock_service,
)

from custom_components.kd_brain.const import (
    CONF_CONTROL_MODE,
    CONF_ENABLE_EV,
    CONF_EV_CONNECTED_ENTITY,
    CONF_EV_CURRENT_CONTROL_ENTITY,
    CONF_GRID_POWER_ENTITY,
    CONTROL_ACTIVE,
    DOMAIN,
)
from custom_components.kd_brain.data.models import (
    EvState,
    GridState,
    PricePoint,
    PriceSeries,
    SystemState,
    Telemetry,
)
from custom_components.kd_brain.ev.config import EvConfig
from custom_components.kd_brain.ev.planner import plan_ev
from custom_components.kd_brain.ev.safety import ev_safety
from custom_components.kd_brain.safety.state import ControlState

from .conftest import OPTIONS

NOW = datetime(2026, 6, 28, 10, 0, tzinfo=UTC)


def _point(hour: int, market: float) -> PricePoint:
    start = datetime(2026, 6, 28, hour, 0, tzinfo=UTC)
    value = Decimal(str(market))
    return PricePoint(start, start + timedelta(hours=1), value, value, value)


def _state(prices: list[tuple[int, float]], telemetry: Telemetry) -> SystemState:
    series = PriceSeries(
        points=tuple(_point(h, m) for h, m in prices), resolution=timedelta(hours=1)
    )
    return SystemState(ts=NOW, prices=series, telemetry=telemetry)


def _config(**overrides: object) -> EvConfig:
    return replace(EvConfig.from_options({CONF_ENABLE_EV: True}), **overrides)


# --- Planner ---------------------------------------------------------------


def test_plan_charges_on_cheap_price() -> None:
    plan = plan_ev(_state([(10, 0.10), (11, 0.30)], Telemetry()), _config())
    assert plan.current_a == 16  # max current on cheap price


def test_plan_charges_on_solar_surplus() -> None:
    telemetry = Telemetry(grid=GridState(power_w=-2000.0))
    plan = plan_ev(_state([(10, 0.20), (11, 0.20)], telemetry), _config())
    assert plan.current_a == 8  # 2000 W / 230 V (1 phase)


def test_plan_stops_when_disconnected() -> None:
    telemetry = Telemetry(ev=EvState(connected=False))
    assert plan_ev(_state([(10, 0.10)], telemetry), _config()).current_a == 0


def test_plan_stops_at_target_soc() -> None:
    telemetry = Telemetry(ev=EvState(soc=85.0))
    plan = plan_ev(_state([(10, 0.10)], telemetry), _config(target_soc=80.0))
    assert plan.current_a == 0


def test_plan_disabled() -> None:
    assert (
        plan_ev(_state([(10, 0.10)], Telemetry()), _config(enabled=False)).current_a
        == 0
    )


# --- Safety ----------------------------------------------------------------


def test_safety_iec_snaps_below_minimum_to_zero() -> None:
    current, _write, reasons = ev_safety(3, _config(), ControlState(), NOW)
    assert current == 0
    assert any("IEC" in r for r in reasons)


def test_safety_clamps_to_maximum() -> None:
    current, _write, reasons = ev_safety(20, _config(max_a=16), ControlState(), NOW)
    assert current == 16
    assert any("geklemd" in r for r in reasons)


def test_safety_anti_oscillation_blocks_quick_on() -> None:
    state = ControlState(
        last_written_w=0,
        last_write_ts=NOW - timedelta(seconds=10),
        last_direction="idle",
        last_change_ts=NOW - timedelta(seconds=10),
    )
    _current, write, reasons = ev_safety(16, _config(min_dwell_s=300), state, NOW)
    assert write is False
    assert any("anti-oscillatie" in r for r in reasons)


# --- Integration -----------------------------------------------------------


async def test_ev_active_mode_writes_current(hass: HomeAssistant, mock_epex) -> None:
    """In active mode a solar-driven charge current is written."""
    calls = async_mock_service(hass, "number", "set_value")
    await hass.config.async_set_time_zone("Europe/Amsterdam")
    with freeze_time("2026-06-28T08:30:00+00:00"):
        hass.states.async_set("binary_sensor.ev", "on")
        hass.states.async_set("sensor.grid", "-3000", {"unit_of_measurement": "W"})
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="KD Brain",
            data={},
            options={
                **OPTIONS,
                CONF_GRID_POWER_ENTITY: "sensor.grid",
                CONF_ENABLE_EV: True,
                CONF_EV_CONNECTED_ENTITY: "binary_sensor.ev",
                CONF_EV_CURRENT_CONTROL_ENTITY: "number.ev_current",
                CONF_CONTROL_MODE: CONTROL_ACTIVE,
            },
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert len(calls) >= 1
        assert 6 <= calls[-1].data["value"] <= 16

        ent_reg = er.async_get(hass)
        sensor = ent_reg.async_get_entity_id(
            "sensor", DOMAIN, f"{entry.entry_id}_recommended_ev_current"
        )
        assert sensor is not None
        assert int(hass.states.get(sensor).state) >= 6  # type: ignore[union-attr]
