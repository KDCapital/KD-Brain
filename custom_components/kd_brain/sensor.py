"""Price sensors for KD Brain."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.util import dt as dt_util

from . import KDBrainConfigEntry
from .const import (
    CONF_PRICE_INTERVAL,
    CURRENCY_PER_KWH,
    DEFAULT_PRICE_INTERVAL,
    INTERVAL_HOURLY,
    PRICE_PRECISION,
)
from .coordinator import KDBrainPriceCoordinator
from .data.models import PriceSeries
from .entity import KDBrainPriceEntity


def _display_series(coordinator: KDBrainPriceCoordinator) -> PriceSeries:
    """Return the price series at the user's chosen display resolution."""
    series = coordinator.data
    assert coordinator.config_entry is not None
    interval = coordinator.config_entry.options.get(
        CONF_PRICE_INTERVAL, DEFAULT_PRICE_INTERVAL
    )
    return series.to_hourly() if interval == INTERVAL_HOURLY else series


def _today_series(coordinator: KDBrainPriceCoordinator) -> PriceSeries:
    """Return the display series sliced to the local calendar day."""
    today = dt_util.now().date()
    return _display_series(coordinator).slice_local_day(
        today, dt_util.DEFAULT_TIME_ZONE
    )


def _round(value: Decimal | None) -> float | None:
    """Round a price for display, preserving ``None``."""
    return None if value is None else round(float(value), PRICE_PRECISION)


def _current_all_in(coordinator: KDBrainPriceCoordinator) -> float | None:
    point = _display_series(coordinator).point_at(dt_util.utcnow())
    return _round(point.all_in) if point else None


def _current_market(coordinator: KDBrainPriceCoordinator) -> float | None:
    point = _display_series(coordinator).point_at(dt_util.utcnow())
    return _round(point.market) if point else None


def _current_feed_in(coordinator: KDBrainPriceCoordinator) -> float | None:
    point = _display_series(coordinator).point_at(dt_util.utcnow())
    return _round(point.feed_in) if point else None


def _next_all_in(coordinator: KDBrainPriceCoordinator) -> float | None:
    point = _display_series(coordinator).next_point(dt_util.utcnow())
    return _round(point.all_in) if point else None


def _min_today(coordinator: KDBrainPriceCoordinator) -> float | None:
    point = _today_series(coordinator).min_point()
    return _round(point.all_in) if point else None


def _max_today(coordinator: KDBrainPriceCoordinator) -> float | None:
    point = _today_series(coordinator).max_point()
    return _round(point.all_in) if point else None


def _avg_today(coordinator: KDBrainPriceCoordinator) -> float | None:
    return _round(_today_series(coordinator).average_all_in())


def _data_attributes(coordinator: KDBrainPriceCoordinator) -> dict[str, Any]:
    """Expose the full price curve for dashboards/charts."""
    series = coordinator.data
    tz = dt_util.DEFAULT_TIME_ZONE
    local = dt_util.now()
    today = series.slice_local_day(local.date(), tz)
    tomorrow = series.slice_local_day((local + timedelta(days=1)).date(), tz)
    return {
        "source": coordinator.config_entry.options.get("price_source")
        if coordinator.config_entry
        else None,
        "today": today.as_dicts(),
        "tomorrow": tomorrow.as_dicts(),
        "today_hourly": today.to_hourly().as_dicts(),
        "tomorrow_hourly": tomorrow.to_hourly().as_dicts(),
    }


@dataclass(frozen=True, kw_only=True)
class KDBrainPriceSensorDescription(SensorEntityDescription):
    """Describes a KD Brain price sensor."""

    value_fn: Callable[[KDBrainPriceCoordinator], StateType]
    attr_fn: Callable[[KDBrainPriceCoordinator], dict[str, Any]] | None = None


SENSORS: tuple[KDBrainPriceSensorDescription, ...] = (
    KDBrainPriceSensorDescription(
        key="current_price",
        translation_key="current_price",
        native_unit_of_measurement=CURRENCY_PER_KWH,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=PRICE_PRECISION,
        value_fn=_current_all_in,
    ),
    KDBrainPriceSensorDescription(
        key="current_market_price",
        translation_key="current_market_price",
        native_unit_of_measurement=CURRENCY_PER_KWH,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=PRICE_PRECISION,
        value_fn=_current_market,
    ),
    KDBrainPriceSensorDescription(
        key="current_feed_in_price",
        translation_key="current_feed_in_price",
        native_unit_of_measurement=CURRENCY_PER_KWH,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=PRICE_PRECISION,
        value_fn=_current_feed_in,
    ),
    KDBrainPriceSensorDescription(
        key="next_price",
        translation_key="next_price",
        native_unit_of_measurement=CURRENCY_PER_KWH,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=PRICE_PRECISION,
        value_fn=_next_all_in,
    ),
    KDBrainPriceSensorDescription(
        key="min_price_today",
        translation_key="min_price_today",
        native_unit_of_measurement=CURRENCY_PER_KWH,
        suggested_display_precision=PRICE_PRECISION,
        value_fn=_min_today,
    ),
    KDBrainPriceSensorDescription(
        key="max_price_today",
        translation_key="max_price_today",
        native_unit_of_measurement=CURRENCY_PER_KWH,
        suggested_display_precision=PRICE_PRECISION,
        value_fn=_max_today,
    ),
    KDBrainPriceSensorDescription(
        key="average_price_today",
        translation_key="average_price_today",
        native_unit_of_measurement=CURRENCY_PER_KWH,
        suggested_display_precision=PRICE_PRECISION,
        value_fn=_avg_today,
    ),
    KDBrainPriceSensorDescription(
        key="price_data",
        translation_key="price_data",
        native_unit_of_measurement=CURRENCY_PER_KWH,
        suggested_display_precision=PRICE_PRECISION,
        value_fn=_current_all_in,
        attr_fn=_data_attributes,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: KDBrainConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up KD Brain price sensors."""
    coordinator = entry.runtime_data.price_coordinator
    async_add_entities(
        KDBrainPriceSensor(coordinator, description) for description in SENSORS
    )


class KDBrainPriceSensor(KDBrainPriceEntity, SensorEntity):
    """A price sensor backed by the price coordinator."""

    entity_description: KDBrainPriceSensorDescription

    def __init__(
        self,
        coordinator: KDBrainPriceCoordinator,
        description: KDBrainPriceSensorDescription,
    ) -> None:
        """Initialise the sensor."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> StateType:
        """Return the sensor value."""
        return self.entity_description.value_fn(self.coordinator)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra attributes for charting sensors."""
        if self.entity_description.attr_fn is None:
            return None
        return self.entity_description.attr_fn(self.coordinator)
