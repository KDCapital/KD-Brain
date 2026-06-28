"""Data update coordinator for KD Brain prices."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import (
    CALLBACK_TYPE,
    Event,
    EventStateChangedData,
    HomeAssistant,
    callback,
)
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    CONF_PRICE_SOURCE,
    CONF_UPDATE_INTERVAL_MINUTES,
    DEFAULT_PRICE_SOURCE,
    DEFAULT_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
    EVENT_DECISION,
    EVENT_PRICES_UPDATED,
    ISSUE_PRICE_SOURCE_UNAVAILABLE,
    MAX_UPDATE_INTERVAL_MINUTES,
    MIN_UPDATE_INTERVAL_MINUTES,
    PRICE_SOURCE_EPEXPRIJZEN,
)
from .data.adapters.entity_adapter import EntityAdapter
from .data.models import PriceSeries, Telemetry
from .data.sources.base import PriceSource, PriceSourceError
from .data.sources.epexprijzen import EpexPrijzenSource
from .economics import TariffConfig
from .engine.config import OptimizerConfig
from .engine.decision import Decision
from .engine.optimizer import optimize
from .engine.state import build_system_state

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


class KDBrainTelemetryCoordinator(DataUpdateCoordinator[Telemetry]):
    """Push-based coordinator for device telemetry read from HA entities.

    It does not poll: it reads the configured source entities once and then
    refreshes whenever any of them changes state.
    """

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialise the coordinator from a config entry."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_telemetry",
            update_interval=None,
            config_entry=entry,
        )
        self._adapter = EntityAdapter(dict(entry.options))

    @property
    def adapter(self) -> EntityAdapter:
        """Return the underlying entity adapter."""
        return self._adapter

    async def _async_update_data(self) -> Telemetry:
        """Read the latest telemetry snapshot from source entities."""
        return self._adapter.read(self.hass)

    @callback
    def async_setup_listeners(self) -> CALLBACK_TYPE:
        """Subscribe to source-entity changes; return an unsubscribe callback."""
        entity_ids = self._adapter.entity_ids
        if not entity_ids:
            return lambda: None
        return async_track_state_change_event(
            self.hass, entity_ids, self._handle_source_change
        )

    @callback
    def _handle_source_change(self, event: Event[EventStateChangedData]) -> None:
        """Rebuild telemetry when a tracked entity changes."""
        self.async_set_updated_data(self._adapter.read(self.hass))


class KDBrainOptimizationCoordinator(DataUpdateCoordinator[Decision | None]):
    """Runs the optimisation engine whenever prices or telemetry change.

    The coordinator does not poll. It listens to the price and telemetry
    coordinators and recomputes a fresh :class:`Decision` (debounced by the
    built-in request-refresh debouncer). KD Brain stays in observe-only mode in
    M3: the decision is a recommendation, nothing is actuated.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        price_coordinator: KDBrainPriceCoordinator,
        telemetry_coordinator: KDBrainTelemetryCoordinator,
    ) -> None:
        """Initialise the coordinator from the upstream coordinators."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_optimization",
            update_interval=None,
            config_entry=entry,
        )
        self._price = price_coordinator
        self._telemetry = telemetry_coordinator

    @property
    def optimizer_config(self) -> OptimizerConfig:
        """Return the engine config built from the current entry options."""
        assert self.config_entry is not None
        return OptimizerConfig.from_options(dict(self.config_entry.options))

    async def _async_update_data(self) -> Decision | None:
        """Build a system state and run the optimiser."""
        prices = self._price.data
        if prices is None or prices.is_empty:
            return None
        telemetry = self._telemetry.data or Telemetry()
        state = build_system_state(dt_util.utcnow(), prices, telemetry)
        decision = optimize(state, self.optimizer_config)
        self.hass.bus.async_fire(
            EVENT_DECISION,
            {"action": decision.chosen.action.value, "strategy": decision.strategy},
        )
        return decision

    @callback
    def async_setup_listeners(self) -> list[CALLBACK_TYPE]:
        """Recompute whenever prices or telemetry update."""
        return [
            self._price.async_add_listener(self._handle_upstream),
            self._telemetry.async_add_listener(self._handle_upstream),
        ]

    @callback
    def _handle_upstream(self) -> None:
        """Schedule a debounced recompute on an upstream update."""
        self.hass.async_create_task(self.async_request_refresh())
