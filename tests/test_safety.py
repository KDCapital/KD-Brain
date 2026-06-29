"""Unit tests for the safety gate."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

from custom_components.kd_brain.data.models import BatteryState, Telemetry
from custom_components.kd_brain.engine.decision import Action, BatteryAction
from custom_components.kd_brain.safety.config import SafetyConfig
from custom_components.kd_brain.safety.gate import evaluate
from custom_components.kd_brain.safety.state import ControlState

NOW = datetime(2026, 6, 28, 12, 0, tzinfo=UTC)


def _config(**overrides: object) -> SafetyConfig:
    return replace(SafetyConfig.from_options({}), **overrides)


def _action(kind: BatteryAction, power: int) -> Action:
    return Action(device="battery", action=kind, power_w=power, reason="test")


def _soc(value: float) -> Telemetry:
    return Telemetry(batteries=(BatteryState(soc=value),))


def test_soc_blocks_charge_when_full() -> None:
    outcome = evaluate(
        _action(BatteryAction.CHARGE, 2000), _soc(96.0), ControlState(), _config(), NOW
    )
    assert outcome.action.action is BatteryAction.IDLE
    assert outcome.signed_w == 0
    assert any("geblokkeerd" in r for r in outcome.reasons)


def test_soc_blocks_discharge_when_empty() -> None:
    outcome = evaluate(
        _action(BatteryAction.DISCHARGE, 2000),
        _soc(5.0),
        ControlState(),
        _config(),
        NOW,
    )
    assert outcome.action.action is BatteryAction.IDLE


def test_power_is_clamped() -> None:
    outcome = evaluate(
        _action(BatteryAction.CHARGE, 9000),
        Telemetry(),
        ControlState(),
        _config(max_charge_w=2500),
        NOW,
    )
    assert outcome.signed_w == 2500
    assert any("geklemd" in r for r in outcome.reasons)


def test_write_throttle_blocks_recent_write() -> None:
    state = ControlState(
        last_written_w=1000,
        last_write_ts=NOW - timedelta(seconds=10),
        last_direction="charge",
        last_change_ts=NOW - timedelta(seconds=1000),
    )
    outcome = evaluate(
        _action(BatteryAction.CHARGE, 2000), Telemetry(), state, _config(), NOW
    )
    assert outcome.write is False
    assert any("throttle" in r for r in outcome.reasons)


def test_no_write_when_unchanged() -> None:
    state = ControlState(
        last_written_w=2000,
        last_write_ts=NOW - timedelta(seconds=1000),
        last_direction="charge",
        last_change_ts=NOW - timedelta(seconds=1000),
    )
    outcome = evaluate(
        _action(BatteryAction.CHARGE, 2000), Telemetry(), state, _config(), NOW
    )
    assert outcome.write is False
    assert any("ongewijzigd" in r for r in outcome.reasons)


def test_anti_oscillation_blocks_quick_reversal() -> None:
    state = ControlState(
        last_written_w=-1000,
        last_write_ts=NOW - timedelta(seconds=1000),
        last_direction="discharge",
        last_change_ts=NOW - timedelta(seconds=100),
    )
    outcome = evaluate(
        _action(BatteryAction.CHARGE, 2000),
        Telemetry(),
        state,
        _config(min_dwell_s=300),
        NOW,
    )
    assert outcome.write is False
    assert any("anti-oscillatie" in r for r in outcome.reasons)


def test_idle_stop_always_allowed() -> None:
    state = ControlState(
        last_written_w=2000,
        last_write_ts=NOW - timedelta(seconds=1),
        last_direction="charge",
        last_change_ts=NOW - timedelta(seconds=1),
    )
    outcome = evaluate(
        _action(BatteryAction.IDLE, 0), Telemetry(), state, _config(), NOW
    )
    assert outcome.signed_w == 0
    assert outcome.write is True


def test_control_state_records_direction_change() -> None:
    state = ControlState()
    state.record(1500, NOW)
    assert state.last_direction == "charge"
    assert state.last_written_w == 1500
    assert state.last_change_ts == NOW
