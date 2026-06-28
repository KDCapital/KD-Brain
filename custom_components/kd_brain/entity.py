"""Base entity for KD Brain."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import KDBrainPriceCoordinator


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
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="KD Brain",
            manufacturer=MANUFACTURER,
            model=MODEL,
            entry_type=None,
        )
