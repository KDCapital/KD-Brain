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
from .coordinator import KDBrainPriceCoordinator, KDBrainTelemetryCoordinator
from .services import async_setup_services, async_unload_services

type KDBrainConfigEntry = ConfigEntry[KDBrainRuntimeData]


@dataclass(slots=True)
class KDBrainRuntimeData:
    """Runtime data stored on the config entry.

    Acts as the composition root for KD Brain's layers. It currently holds the
    price and telemetry coordinators; subsequent milestones extend it (energy
    engine, strategy registry, safety registry, actuator registry).
    """

    price_coordinator: KDBrainPriceCoordinator
    telemetry_coordinator: KDBrainTelemetryCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: KDBrainConfigEntry) -> bool:
    """Set up KD Brain from a config entry."""
    price_coordinator = KDBrainPriceCoordinator(hass, entry)
    await price_coordinator.async_config_entry_first_refresh()

    telemetry_coordinator = KDBrainTelemetryCoordinator(hass, entry)
    await telemetry_coordinator.async_config_entry_first_refresh()
    entry.async_on_unload(telemetry_coordinator.async_setup_listeners())

    entry.runtime_data = KDBrainRuntimeData(
        price_coordinator=price_coordinator,
        telemetry_coordinator=telemetry_coordinator,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    async_setup_services(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: KDBrainConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        async_unload_services(hass)
    return unloaded


async def _async_update_listener(
    hass: HomeAssistant, entry: KDBrainConfigEntry
) -> None:
    """Reload the entry when its options change."""
    await hass.config_entries.async_reload(entry.entry_id)
