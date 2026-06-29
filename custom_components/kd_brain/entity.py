"""Base entities for KD Brain."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import (
    KDBrainActuationCoordinator,
    KDBrainOptimizationCoordinator,
    KDBrainPriceCoordinator,
    KDBrainTelemetryCoordinator,
)


def kd_brain_device_info(entry_id: str) -> DeviceInfo:
    """Return the shared device info so all entities group under one device."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry_id)},
        name="KD Brain",
        manufacturer=MANUFACTURER,
        model=MODEL,
        entry_type=None,
    )


class KDBrainPriceEntity(CoordinatorEntity[KDBrainPriceCoordinator]):
    """Base class for entities backed by the price coordinator.

    All KD Brain entities for a single config entry share one logical device so
    they group together cleanly in the Home Assistant UI.
    """

    _attr_has_entity_name = True

    def __init__(self, coordinator: KDBrainPriceCoordinator, key: str) -> None:
        """Initialise the entity with a stable unique id and device."""
        super().__init__(coordinator)
        assert coordinator.config_entry is not None
        entry_id = coordinator.config_entry.entry_id
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_device_info = kd_brain_device_info(entry_id)


class KDBrainTelemetryEntity(CoordinatorEntity[KDBrainTelemetryCoordinator]):
    """Base class for entities backed by the telemetry coordinator."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: KDBrainTelemetryCoordinator, key: str) -> None:
        """Initialise the entity with a stable unique id and device."""
        super().__init__(coordinator)
        assert coordinator.config_entry is not None
        entry_id = coordinator.config_entry.entry_id
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_device_info = kd_brain_device_info(entry_id)


class KDBrainOptimizationEntity(CoordinatorEntity[KDBrainOptimizationCoordinator]):
    """Base class for entities backed by the optimisation coordinator."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: KDBrainOptimizationCoordinator, key: str) -> None:
        """Initialise the entity with a stable unique id and device."""
        super().__init__(coordinator)
        assert coordinator.config_entry is not None
        entry_id = coordinator.config_entry.entry_id
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_device_info = kd_brain_device_info(entry_id)


class KDBrainActuationEntity(CoordinatorEntity[KDBrainActuationCoordinator]):
    """Base class for entities backed by the actuation coordinator."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: KDBrainActuationCoordinator, key: str) -> None:
        """Initialise the entity with a stable unique id and device."""
        super().__init__(coordinator)
        assert coordinator.config_entry is not None
        entry_id = coordinator.config_entry.entry_id
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_device_info = kd_brain_device_info(entry_id)
