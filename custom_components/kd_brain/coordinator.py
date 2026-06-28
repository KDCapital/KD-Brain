"""Data update coordinator for KD Brain prices."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    CONF_PRICE_SOURCE,
    CONF_UPDATE_INTERVAL_MINUTES,
    DEFAULT_PRICE_SOURCE,
    DEFAULT_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
    EVENT_PRICES_UPDATED,
    ISSUE_PRICE_SOURCE_UNAVAILABLE,
    MAX_UPDATE_INTERVAL_MINUTES,
    MIN_UPDATE_INTERVAL_MINUTES,
    PRICE_SOURCE_EPEXPRIJZEN,
)
from .data.models import PriceSeries
from .data.sources.base import PriceSource, PriceSourceError
from .data.sources.epexprijzen import EpexPrijzenSource
from .economics import TariffConfig

_LOGGER = logging.getLogger(__name__)


def _build_source(hass: HomeAssistant, source_id: str) -> PriceSource:
    """Construct the configured price source (extend as providers are added)."""
    session = async_get_clientsession(hass)
    if source_id == PRICE_SOURCE_EPEXPRIJZEN:
        return EpexPrijzenSource(session)
    # Unknown source ids fall back to the default to keep the entry usable.
    _LOGGER.warning("Unknown price source %r, falling back to default", source_id)
    return EpexPrijzenSource(session)


class KDBrainPriceCoordinator(DataUpdateCoordinator[PriceSeries]):
    """Coordinates fetching day-ahead prices and applying the tariff model."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialise the coordinator from a config entry."""
        minutes = int(
            entry.options.get(
                CONF_UPDATE_INTERVAL_MINUTES, DEFAULT_UPDATE_INTERVAL_MINUTES
            )
        )
        minutes = max(
            MIN_UPDATE_INTERVAL_MINUTES, min(MAX_UPDATE_INTERVAL_MINUTES, minutes)
        )
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=minutes),
            config_entry=entry,
        )
        source_id = entry.options.get(CONF_PRICE_SOURCE, DEFAULT_PRICE_SOURCE)
        self._source = _build_source(hass, source_id)

    @property
    def tariff(self) -> TariffConfig:
        """Return the tariff model built from the current entry options."""
        assert self.config_entry is not None
        return TariffConfig.from_options(dict(self.config_entry.options))

    async def _async_update_data(self) -> PriceSeries:
        """Fetch fresh prices, manage the availability repair, and notify."""
        try:
            series = await self._source.async_fetch(dt_util.utcnow(), self.tariff)
        except PriceSourceError as err:
            self._async_raise_issue()
            raise UpdateFailed(str(err)) from err

        self._async_clear_issue()
        self.hass.bus.async_fire(EVENT_PRICES_UPDATED, {"points": len(series.points)})
        return series

    def _async_raise_issue(self) -> None:
        """Register a repair issue when the price source is unavailable."""
        ir.async_create_issue(
            self.hass,
            DOMAIN,
            ISSUE_PRICE_SOURCE_UNAVAILABLE,
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key=ISSUE_PRICE_SOURCE_UNAVAILABLE,
            translation_placeholders={"source": self._source.name},
        )

    def _async_clear_issue(self) -> None:
        """Clear the price-source availability repair issue."""
        ir.async_delete_issue(self.hass, DOMAIN, ISSUE_PRICE_SOURCE_UNAVAILABLE)
