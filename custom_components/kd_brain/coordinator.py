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

from .actuators.base import ActuationResult
from .actuators.entity import EntityActuator
from .actuators.registry import build_actuator
from .const import (
    CONF_PRICE_SOURCE,
    CONF_UPDATE_INTERVAL_MINUTES,
    DEFAULT_PRICE_SOURCE,
    DEFAULT_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
    EVENT_ACTUATION,
    EVENT_DECISION,
    EVENT_PRICES_UPDATED,
    ISSUE_MILP_UNAVAILABLE,
    ISSUE_PRICE_SOURCE_UNAVAILABLE,
    MAX_UPDATE_INTERVAL_MINUTES,
    MIN_UPDATE_INTERVAL_MINUTES,
    OPTIMIZER_MILP,
    PRICE_SOURCE_EPEXPRIJZEN,
)
from .data.adapters.entity_adapter import EntityAdapter
from .data.models import Forecast, PriceSeries, SystemState, Telemetry
from .data.sources.base import PriceSource, PriceSourceError
from .data.sources.epexprijzen import EpexPrijzenSource
from .economics import TariffConfig
from .engine.config import OptimizerConfig
from .engine.decision import Decision
from .engine.forecaster import build_forecaster
from .engine.milp import MilpUnavailableError, milp_optimize
from .engine.optimizer import optimize
from .engine.state import build_system_state
from .ev.config import EvConfig
from .ev.planner import EvResult, plan_ev
from .ev.safety import ev_safety
from .safety.config import SafetyConfig
from .safety.gate import evaluate
from .safety.state import ControlState

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
        self._forecaster = build_forecaster(dict(entry.options))
        self._forecast = Forecast()

    @property
    def optimizer_config(self) -> OptimizerConfig:
        """Return the engine config built from the current entry options."""
        assert self.config_entry is not None
        return OptimizerConfig.from_options(dict(self.config_entry.options))

    @property
    def forecast(self) -> Forecast:
        """Return the most recent forecast."""
        return self._forecast

    async def _async_update_data(self) -> Decision | None:
        """Build a system state and run the optimiser."""
        prices = self._price.data
        if prices is None or prices.is_empty:
            return None
        telemetry = self._telemetry.data or Telemetry()
        config = self.optimizer_config
        self._forecast = self._forecaster.predict(self.hass)
        state = build_system_state(dt_util.utcnow(), prices, telemetry, self._forecast)
        decision = self._decide(state, config)
        self.hass.bus.async_fire(
            EVENT_DECISION,
            {"action": decision.chosen.action.value, "strategy": decision.strategy},
        )
        return decision

    def _decide(self, state: SystemState, config: OptimizerConfig) -> Decision:
        """Run the configured optimiser, falling back to the heuristic."""
        if config.optimizer_mode != OPTIMIZER_MILP:
            return optimize(state, config)
        try:
            decision = milp_optimize(state, config)
        except MilpUnavailableError:
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                ISSUE_MILP_UNAVAILABLE,
                is_fixable=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key=ISSUE_MILP_UNAVAILABLE,
            )
            return optimize(state, config)
        ir.async_delete_issue(self.hass, DOMAIN, ISSUE_MILP_UNAVAILABLE)
        return decision if decision is not None else optimize(state, config)

    @callback
    def async_setup_listeners(self) -> list[CALLBACK_TYPE]:
        """Recompute whenever prices, telemetry or forecast entities update."""
        listeners = [
            self._price.async_add_listener(self._handle_upstream),
            self._telemetry.async_add_listener(self._handle_upstream),
        ]
        forecast_ids = self._forecaster.entity_ids
        if forecast_ids:
            listeners.append(
                async_track_state_change_event(
                    self.hass, forecast_ids, self._handle_forecast_change
                )
            )
        return listeners

    @callback
    def _handle_upstream(self) -> None:
        """Schedule a debounced recompute on an upstream update."""
        self.hass.async_create_task(self.async_request_refresh())

    @callback
    def _handle_forecast_change(self, event: Event[EventStateChangedData]) -> None:
        """Schedule a recompute when a forecast entity changes."""
        self.hass.async_create_task(self.async_request_refresh())


class KDBrainActuationCoordinator(DataUpdateCoordinator[ActuationResult | None]):
    """Runs every decision through the safety gate and (optionally) actuates.

    In observe-only mode it evaluates and reports what would happen but never
    writes. In active mode it writes the safety-approved setpoint via the
    actuator, subject to throttling, hysteresis and anti-oscillation.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        optimization_coordinator: KDBrainOptimizationCoordinator,
        telemetry_coordinator: KDBrainTelemetryCoordinator,
    ) -> None:
        """Initialise from the optimisation and telemetry coordinators."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_actuation",
            update_interval=None,
            config_entry=entry,
        )
        self._optimization = optimization_coordinator
        self._telemetry = telemetry_coordinator
        self._control_state = ControlState()
        self._actuator = build_actuator(dict(entry.options))

    @property
    def safety_config(self) -> SafetyConfig:
        """Return the safety config built from the current entry options."""
        assert self.config_entry is not None
        return SafetyConfig.from_options(dict(self.config_entry.options))

    async def _async_update_data(self) -> ActuationResult | None:
        """Evaluate the latest decision through safety and actuate if active."""
        decision = self._optimization.data
        if decision is None:
            return None
        telemetry = self._telemetry.data or Telemetry()
        config = self.safety_config
        now = dt_util.utcnow()

        outcome = evaluate(decision.chosen, telemetry, self._control_state, config, now)

        written = False
        if config.is_active and self._actuator.is_configured and outcome.write:
            await self._actuator.async_apply(self.hass, outcome.signed_w)
            self._control_state.record(outcome.signed_w, now)
            written = True

        result = ActuationResult(
            ts=now,
            mode=config.control_mode,
            intended=decision.chosen,
            outcome=outcome,
            written=written,
        )
        self.hass.bus.async_fire(
            EVENT_ACTUATION,
            {
                "mode": config.control_mode,
                "written": written,
                "action": outcome.action.action.value,
                "power_w": outcome.signed_w,
            },
        )
        return result

    @callback
    def async_setup_listeners(self) -> list[CALLBACK_TYPE]:
        """Re-evaluate whenever a new decision is produced."""
        return [self._optimization.async_add_listener(self._handle_upstream)]

    @callback
    def _handle_upstream(self) -> None:
        """Schedule an actuation pass on a new decision."""
        self.hass.async_create_task(self.async_request_refresh())


class KDBrainEvCoordinator(DataUpdateCoordinator[EvResult | None]):
    """Plans EV charging and (in active mode) sets the charge current.

    Mirrors the battery actuation pipeline but for an EV charger: it picks a
    charge current from prices, solar surplus and the target SOC, applies the
    IEC 61851 and anti-oscillation safety clamps, and writes the current to the
    configured control entity only in active mode.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        price_coordinator: KDBrainPriceCoordinator,
        telemetry_coordinator: KDBrainTelemetryCoordinator,
    ) -> None:
        """Initialise from the price and telemetry coordinators."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_ev",
            update_interval=None,
            config_entry=entry,
        )
        self._price = price_coordinator
        self._telemetry = telemetry_coordinator
        self._control_state = ControlState()
        config = EvConfig.from_options(dict(entry.options))
        self._actuator = (
            EntityActuator(config.control_entity) if config.control_entity else None
        )

    @property
    def ev_config(self) -> EvConfig:
        """Return the EV config built from the current entry options."""
        assert self.config_entry is not None
        return EvConfig.from_options(dict(self.config_entry.options))

    async def _async_update_data(self) -> EvResult | None:
        """Plan EV charging and apply it when active."""
        config = self.ev_config
        if not config.enabled:
            return None
        prices = self._price.data
        if prices is None or prices.is_empty:
            return None
        telemetry = self._telemetry.data or Telemetry()
        now = dt_util.utcnow()
        state = build_system_state(now, prices, telemetry)

        plan = plan_ev(state, config)
        current, write, reasons = ev_safety(
            plan.current_a, config, self._control_state, now
        )

        written = False
        if config.is_active and self._actuator is not None and write:
            await self._actuator.async_apply(self.hass, current)
            self._control_state.record(current, now)
            written = True

        return EvResult(
            ts=now,
            mode=config.control_mode,
            connected=telemetry.ev.connected,
            current_a=current,
            written=written,
            reasons=(plan.reason, *reasons),
        )

    @callback
    def async_setup_listeners(self) -> list[CALLBACK_TYPE]:
        """Re-plan whenever prices or telemetry update."""
        return [
            self._price.async_add_listener(self._handle_upstream),
            self._telemetry.async_add_listener(self._handle_upstream),
        ]

    @callback
    def _handle_upstream(self) -> None:
        """Schedule an EV planning pass on an upstream update."""
        self.hass.async_create_task(self.async_request_refresh())
