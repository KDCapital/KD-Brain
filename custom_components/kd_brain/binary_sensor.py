"""Binary sensors for KD Brain."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from . import KDBrainConfigEntry
from .const import (
    CONF_ENABLE_EV,
    CONF_PRICE_LOW_THRESHOLD,
    DEFAULT_PRICE_LOW_THRESHOLD,
    PRICE_PRECISION,
)
from .coordinator import (
    KDBrainActuationCoordinator,
    KDBrainEvCoordinator,
    KDBrainPriceCoordinator,
)
from .data.models import PricePoint
from .entity import KDBrainActuationEntity, KDBrainEvEntity, KDBrainPriceEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: KDBrainConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up KD Brain binary sensors."""
    runtime = entry.runtime_data
    entities: list[BinarySensorEntity] = [
        KDBrainPriceLowBinarySensor(runtime.price_coordinator),
        KDBrainActiveControlBinarySensor(runtime.actuation_coordinator),
        KDBrainSafetyInterventionBinarySensor(runtime.actuation_coordinator),
    ]
    if entry.options.get(CONF_ENABLE_EV):
        entities.append(KDBrainEvConnectedBinarySensor(runtime.ev_coordinator))
    async_add_entities(entities)


class KDBrainPriceLowBinarySensor(KDBrainPriceEntity, BinarySensorEntity):
    """Indicates whether the current all-in price is below the chosen threshold."""

    _attr_translation_key = "price_low"

    def __init__(self, coordinator: KDBrainPriceCoordinator) -> None:
        """Initialise the binary sensor."""
        super().__init__(coordinator, "price_low")

    def _threshold(self) -> Decimal:
        assert self.coordinator.config_entry is not None
        value = self.coordinator.config_entry.options.get(
            CONF_PRICE_LOW_THRESHOLD, float(DEFAULT_PRICE_LOW_THRESHOLD)
        )
        return Decimal(str(value))

    def _current_point(self) -> PricePoint | None:
        return self.coordinator.data.point_at(dt_util.utcnow())

    @property
    def is_on(self) -> bool | None:
        """Return whether the price is currently low."""
        point = self._current_point()
        if point is None:
            return None
        return point.all_in <= self._threshold()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose the threshold and current price used for the comparison."""
        point = self._current_point()
        return {
            "threshold": round(float(self._threshold()), PRICE_PRECISION),
            "current_all_in": (
                None if point is None else round(float(point.all_in), PRICE_PRECISION)
            ),
        }


class KDBrainActiveControlBinarySensor(KDBrainActuationEntity, BinarySensorEntity):
    """On when KD Brain is allowed to actively steer hardware."""

    _attr_translation_key = "active_control"

    def __init__(self, coordinator: KDBrainActuationCoordinator) -> None:
        """Initialise the binary sensor."""
        super().__init__(coordinator, "active_control")

    @property
    def is_on(self) -> bool:
        """Return whether active control is enabled."""
        return self.coordinator.safety_config.is_active


class KDBrainSafetyInterventionBinarySensor(KDBrainActuationEntity, BinarySensorEntity):
    """On when the safety layer clamped or blocked the intended action."""

    _attr_translation_key = "safety_intervened"

    def __init__(self, coordinator: KDBrainActuationCoordinator) -> None:
        """Initialise the binary sensor."""
        super().__init__(coordinator, "safety_intervened")

    @property
    def is_on(self) -> bool | None:
        """Return whether safety intervened on the latest decision."""
        result = self.coordinator.data
        return None if result is None else result.intervened

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Expose the safety reasons."""
        result = self.coordinator.data
        return None if result is None else {"reasons": list(result.outcome.reasons)}


class KDBrainEvConnectedBinarySensor(KDBrainEvEntity, BinarySensorEntity):
    """Whether an EV is connected to the charger."""

    _attr_translation_key = "ev_connected"
    _attr_device_class = BinarySensorDeviceClass.PLUG

    def __init__(self, coordinator: KDBrainEvCoordinator) -> None:
        """Initialise the binary sensor."""
        super().__init__(coordinator, "ev_connected")

    @property
    def is_on(self) -> bool | None:
        """Return whether the EV is connected."""
        result = self.coordinator.data
        return None if result is None else result.connected
