"""The KD Brain integration.

KD Brain is an open-source Home Energy Management System (HEMS) for the
Netherlands. Milestone 1 establishes the foundation: dynamic EPEX day-ahead
prices with a fully configurable all-in tariff model.

The integration follows a layered architecture (Data -> Engine -> Strategy ->
Safety -> Actuators). This file wires up the data layer and its coordinator;
later milestones add the remaining layers.
"""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import PLATFORMS
from .coordinator import (
    KDBrainActuationCoordinator,
    KDBrainEvCoordinator,
    KDBrainHeatPumpCoordinator,
    KDBrainOptimizationCoordinator,
    KDBrainPriceCoordinator,
    KDBrainTelemetryCoordinator,
)
from .panel import async_register_frontend, async_unregister_frontend
from .services import async_setup_services, async_unload_services
from .websocket_api import async_register_websocket_api

type KDBrainConfigEntry = ConfigEntry[KDBrainRuntimeData]


@dataclass(slots=True)
class KDBrainRuntimeData:
    """Runtime data stored on the config entry.

    Acts as the composition root for KD Brain's layers. It holds the price and
    telemetry coordinators and the optimisation coordinator (engine); later
    milestones add the safety and actuator registries.
    """

    price_coordinator: KDBrainPriceCoordinator
    telemetry_coordinator: KDBrainTelemetryCoordinator
    optimization_coordinator: KDBrainOptimizationCoordinator
    actuation_coordinator: KDBrainActuationCoordinator
    ev_coordinator: KDBrainEvCoordinator
    heatpump_coordinator: KDBrainHeatPumpCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: KDBrainConfigEntry) -> bool:
    """Set up KD Brain from a config entry."""
    price_coordinator = KDBrainPriceCoordinator(hass, entry)
    await price_coordinator.async_config_entry_first_refresh()

    telemetry_coordinator = KDBrainTelemetryCoordinator(hass, entry)
    await telemetry_coordinator.async_config_entry_first_refresh()
    entry.async_on_unload(telemetry_coordinator.async_setup_listeners())

    optimization_coordinator = KDBrainOptimizationCoordinator(
        hass, entry, price_coordinator, telemetry_coordinator
    )
    await optimization_coordinator.async_refresh()
    for unsub in optimization_coordinator.async_setup_listeners():
        entry.async_on_unload(unsub)

    actuation_coordinator = KDBrainActuationCoordinator(
        hass, entry, optimization_coordinator, telemetry_coordinator
    )
    await actuation_coordinator.async_refresh()
    for unsub in actuation_coordinator.async_setup_listeners():
        entry.async_on_unload(unsub)

    ev_coordinator = KDBrainEvCoordinator(
        hass, entry, price_coordinator, telemetry_coordinator
    )
    await ev_coordinator.async_refresh()
    for unsub in ev_coordinator.async_setup_listeners():
        entry.async_on_unload(unsub)

    heatpump_coordinator = KDBrainHeatPumpCoordinator(
        hass, entry, price_coordinator, telemetry_coordinator
    )
    await heatpump_coordinator.async_refresh()
    for unsub in heatpump_coordinator.async_setup_listeners():
        entry.async_on_unload(unsub)

    entry.runtime_data = KDBrainRuntimeData(
        price_coordinator=price_coordinator,
        telemetry_coordinator=telemetry_coordinator,
        optimization_coordinator=optimization_coordinator,
        actuation_coordinator=actuation_coordinator,
        ev_coordinator=ev_coordinator,
        heatpump_coordinator=heatpump_coordinator,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    async_setup_services(hass)
    async_register_websocket_api(hass)
    await async_register_frontend(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: KDBrainConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        async_unload_services(hass)
        async_unregister_frontend(hass)
    return unloaded


async def _async_update_listener(
    hass: HomeAssistant, entry: KDBrainConfigEntry
) -> None:
    """Reload the entry when its options change."""
    await hass.config_entries.async_reload(entry.entry_id)
