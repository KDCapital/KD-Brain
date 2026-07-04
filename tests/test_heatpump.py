"""Tests for heat pump optimization (planner, safety, integration)."""

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
    CONF_ENABLE_HEATPUMP,
    CONF_HEATPUMP_OFFSET_CONTROL_ENTITY,
    CONF_HEATPUMP_POWER_ENTITY,
    CONTROL_ACTIVE,
    DOMAIN,
)
from custom_components.kd_brain.data.models import (
    PricePoint,
    PriceSeries,
    SystemState,
    Telemetry,
)
from custom_components.kd_brain.heatpump.config import HpConfig
from custom_components.kd_brain.heatpump.planner import plan_heatpump
from custom_components.kd_brain.heatpump.safety import hp_safety
from custom_components.kd_brain.safety.state import ControlState

from .conftest import OPTIONS

NOW = datetime(2026, 6, 28, 10, 0, tzinfo=UTC)


def _point(hour: int, market: float) -> PricePoint:
    start = datetime(2026, 6, 28, hour, 0, tzinfo=UTC)
    value = Decimal(str(market))
    return PricePoint(start, start + timedelta(hours=1), value, value, value)


def _state(prices: list[tuple[int, float]]) -> SystemState:
    series = PriceSeries(
        points=tuple(_point(h, m) for h, m in prices), resolution=timedelta(hours=1)
    )
    return SystemState(ts=NOW, prices=series, telemetry=Telemetry())


def _config(**overrides: object) -> HpConfig:
    return replace(HpConfig.from_options({CONF_ENABLE_HEATPUMP: True}), **overrides)


# --- Planner ---------------------------------------------------------------


def test_plan_preheats_when_cheap() -> None:
    """A price well below average yields a positive (pre-heat) offset."""
    plan = plan_heatpump(_state([(10, 0.05), (11, 0.35)]), _config(max_offset=2.0))
    assert plan.offset_c == 2.0


def test_plan_delays_when_expensive() -> None:
    """A price well above average yields a negative (delay) offset."""
    plan = plan_heatpump(_state([(10, 0.35), (11, 0.05)]), _config(max_offset=2.0))
    assert plan.offset_c == -2.0


def test_plan_neutral_near_average() -> None:
    plan = plan_heatpump(_state([(10, 0.20), (11, 0.20)]), _config())
    assert plan.offset_c == 0.0


def test_plan_disabled() -> None:
    assert plan_heatpump(_state([(10, 0.05)]), _config(enabled=False)).offset_c == 0.0


def test_plan_no_prices() -> None:
    empty = SystemState(
        ts=NOW,
        prices=PriceSeries(points=(), resolution=timedelta(hours=1)),
        telemetry=Telemetry(),
    )
    assert plan_heatpump(empty, _config()).offset_c == 0.0


# --- Safety ----------------------------------------------------------------


def test_safety_clamps_to_maximum() -> None:
    offset, _write, reasons = hp_safety(
        5.0, _config(max_offset=2.0), ControlState(), NOW
    )
    assert offset == 2.0
    assert any("geklemd" in r for r in reasons)


def test_safety_write_throttle_blocks() -> None:
    state = ControlState(
        last_written_w=10,
        last_write_ts=NOW - timedelta(seconds=10),
        last_direction="charge",
        last_change_ts=NOW - timedelta(seconds=10),
    )
    _offset, write, reasons = hp_safety(2.0, _config(write_throttle_s=60), state, NOW)
    assert write is False
    assert any("throttle" in r for r in reasons)


def test_safety_anti_short_cycle_blocks_reversal() -> None:
    state = ControlState(
        last_written_w=-20,
        last_write_ts=NOW - timedelta(seconds=600),
        last_direction="discharge",
        last_change_ts=NOW - timedelta(seconds=10),
    )
    _offset, write, reasons = hp_safety(
        2.0, _config(write_throttle_s=0, min_dwell_s=300), state, NOW
    )
    assert write is False
    assert any("short-cycle" in r for r in reasons)


def test_safety_unchanged_not_rewritten() -> None:
    state = ControlState(
        last_written_w=20,
        last_write_ts=NOW - timedelta(seconds=600),
        last_direction="charge",
        last_change_ts=NOW - timedelta(seconds=600),
    )
    _offset, write, reasons = hp_safety(2.0, _config(write_throttle_s=0), state, NOW)
    assert write is False
    assert any("ongewijzigd" in r for r in reasons)


# --- Integration -----------------------------------------------------------


async def test_heatpump_active_mode_writes_offset(
    hass: HomeAssistant, mock_epex
) -> None:
    """In active mode a price-driven setpoint offset is written."""
    calls = async_mock_service(hass, "number", "set_value")
    await hass.config.async_set_time_zone("Europe/Amsterdam")
    with freeze_time("2026-06-28T08:30:00+00:00"):
        hass.states.async_set("sensor.hp_power", "1200", {"unit_of_measurement": "W"})
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="KD Brain",
            data={},
            options={
                **OPTIONS,
                CONF_ENABLE_HEATPUMP: True,
                CONF_HEATPUMP_POWER_ENTITY: "sensor.hp_power",
                CONF_HEATPUMP_OFFSET_CONTROL_ENTITY: "number.hp_offset",
                CONF_CONTROL_MODE: CONTROL_ACTIVE,
            },
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert len(calls) >= 1
        assert -5.0 <= calls[-1].data["value"] <= 5.0

        ent_reg = er.async_get(hass)
        sensor = ent_reg.async_get_entity_id(
            "sensor", DOMAIN, f"{entry.entry_id}_recommended_heatpump_offset"
        )
        assert sensor is not None
