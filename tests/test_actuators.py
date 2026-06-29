"""Tests for the actuator layer."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.kd_brain.actuators.dry_run import DryRunActuator
from custom_components.kd_brain.actuators.entity import EntityActuator
from custom_components.kd_brain.actuators.registry import build_actuator
from custom_components.kd_brain.const import CONF_BATTERY_POWER_CONTROL_ENTITY


async def test_dry_run_actuator_does_nothing(hass: HomeAssistant) -> None:
    actuator = DryRunActuator()
    assert actuator.is_configured is False
    await actuator.async_apply(hass, 1500)  # must not raise


async def test_entity_actuator_calls_number_set_value(hass: HomeAssistant) -> None:
    calls = async_mock_service(hass, "number", "set_value")
    actuator = EntityActuator("number.battery_power")
    assert actuator.is_configured is True

    await actuator.async_apply(hass, -1200)

    assert len(calls) == 1
    assert calls[0].data["entity_id"] == "number.battery_power"
    assert calls[0].data["value"] == -1200.0


def test_build_actuator_selects_type() -> None:
    assert isinstance(build_actuator({}), DryRunActuator)
    assert isinstance(
        build_actuator({CONF_BATTERY_POWER_CONTROL_ENTITY: "number.x"}),
        EntityActuator,
    )
