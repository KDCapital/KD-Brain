"""Websocket API for the KD Brain custom panel.

Three commands back the sidebar panel:

* ``kd_brain/snapshot`` — a single consolidated JSON blob (prices, telemetry,
  decision, actuation, EV, heat pump, forecast) so the panel can render without
  scraping many entity attributes.
* ``kd_brain/config/get`` — the current options plus the metadata the settings
  tab needs (supplier presets and the enum choices).
* ``kd_brain/config/update`` — validate a partial change against the known
  option allowlist and persist it (admin only), reusing the entry's own reload.
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Any, cast

from homeassistant.components import websocket_api
from homeassistant.components.websocket_api.connection import ActiveConnection
from homeassistant.components.websocket_api.decorators import (
    async_response,
    require_admin,
    websocket_command,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.util import dt as dt_util
import voluptuous as vol

from .const import (
    CONF_BACKUP_RESERVE_SOC,
    CONF_BATTERY_CAPACITY_WH,
    CONF_BATTERY_MAX_SOC,
    CONF_BATTERY_MIN_SOC,
    CONF_BATTERY_POWER_CONTROL_ENTITY,
    CONF_BATTERY_POWER_ENTITIES,
    CONF_BATTERY_SOC_ENTITIES,
    CONF_CONTROL_MODE,
    CONF_DEGRADATION_COST,
    CONF_ENABLE_ARBITRAGE,
    CONF_ENABLE_BACKUP_RESERVE,
    CONF_ENABLE_DYNAMIC_PRICING,
    CONF_ENABLE_EV,
    CONF_ENABLE_HEATPUMP,
    CONF_ENABLE_PEAK_SHAVING,
    CONF_ENABLE_SELF_CONSUMPTION,
    CONF_ENERGY_TAX,
    CONF_EV_CONNECTED_ENTITY,
    CONF_EV_CURRENT_CONTROL_ENTITY,
    CONF_EV_MAX_CURRENT_A,
    CONF_EV_MIN_CURRENT_A,
    CONF_EV_PHASES,
    CONF_EV_POWER_ENTITY,
    CONF_EV_SOC_ENTITY,
    CONF_EV_TARGET_SOC,
    CONF_FEED_IN_MARKUP,
    CONF_GRID_POWER_ENTITY,
    CONF_HEATPUMP_MAX_OFFSET,
    CONF_HEATPUMP_OFFSET_CONTROL_ENTITY,
    CONF_HEATPUMP_POWER_ENTITY,
    CONF_HYSTERESIS_W,
    CONF_IMBALANCE_PRICE_ENTITY,
    CONF_IMBALANCE_UNIT,
    CONF_LOAD_POWER_ENTITY,
    CONF_MAX_CHARGE_POWER_W,
    CONF_MAX_DISCHARGE_POWER_W,
    CONF_MIN_DWELL_SECONDS,
    CONF_MONTHLY_FEE,
    CONF_OPTIMIZER_MODE,
    CONF_PEAK_SHAVE_EXPORT_W,
    CONF_PEAK_SHAVE_IMPORT_W,
    CONF_PRICE_INTERVAL,
    CONF_PRICE_LOW_THRESHOLD,
    CONF_PRICE_SOURCE,
    CONF_PV_FORECAST_POWER_ENTITY,
    CONF_PV_FORECAST_TODAY_ENTITY,
    CONF_PV_POWER_ENTITY,
    CONF_REGULATION_PROFILE,
    CONF_ROUNDTRIP_EFFICIENCY,
    CONF_SAFETY_MARGIN,
    CONF_SUPPLIER,
    CONF_SUPPLIER_MARKUP,
    CONF_UPDATE_INTERVAL_MINUTES,
    CONF_VAT,
    CONF_WRITE_THROTTLE_SECONDS,
    CONTROL_ACTIVE,
    CONTROL_OBSERVE,
    DEFAULT_PRICE_INTERVAL,
    DEFAULT_PRICE_LOW_THRESHOLD,
    DOMAIN,
    IMBALANCE_UNIT_KWH,
    IMBALANCE_UNIT_MWH,
    INTERVAL_HOURLY,
    INTERVAL_QUARTERLY,
    OPTIMIZER_HEURISTIC,
    OPTIMIZER_MILP,
    PRICE_PRECISION,
    REGULATION_CAPACITY,
    REGULATION_NO_SALDERING,
    REGULATION_SALDERING,
)
from .data.providers import MANUAL, PROVIDERS

if TYPE_CHECKING:
    from . import KDBrainConfigEntry

# Every option key the panel is allowed to write. Anything outside this set is
# rejected so the websocket cannot inject arbitrary options.
EDITABLE_OPTION_KEYS: frozenset[str] = frozenset(
    {
        CONF_SUPPLIER,
        CONF_PRICE_SOURCE,
        CONF_PRICE_INTERVAL,
        CONF_REGULATION_PROFILE,
        CONF_ENERGY_TAX,
        CONF_SUPPLIER_MARKUP,
        CONF_FEED_IN_MARKUP,
        CONF_MONTHLY_FEE,
        CONF_VAT,
        CONF_PRICE_LOW_THRESHOLD,
        CONF_UPDATE_INTERVAL_MINUTES,
        CONF_GRID_POWER_ENTITY,
        CONF_PV_POWER_ENTITY,
        CONF_LOAD_POWER_ENTITY,
        CONF_BATTERY_SOC_ENTITIES,
        CONF_BATTERY_POWER_ENTITIES,
        CONF_BATTERY_CAPACITY_WH,
        CONF_PV_FORECAST_POWER_ENTITY,
        CONF_PV_FORECAST_TODAY_ENTITY,
        CONF_EV_CONNECTED_ENTITY,
        CONF_EV_POWER_ENTITY,
        CONF_EV_SOC_ENTITY,
        CONF_HEATPUMP_POWER_ENTITY,
        CONF_IMBALANCE_PRICE_ENTITY,
        CONF_IMBALANCE_UNIT,
        CONF_OPTIMIZER_MODE,
        CONF_ENABLE_SELF_CONSUMPTION,
        CONF_ENABLE_DYNAMIC_PRICING,
        CONF_ENABLE_ARBITRAGE,
        CONF_ENABLE_PEAK_SHAVING,
        CONF_ENABLE_BACKUP_RESERVE,
        CONF_PEAK_SHAVE_IMPORT_W,
        CONF_PEAK_SHAVE_EXPORT_W,
        CONF_BACKUP_RESERVE_SOC,
        CONF_DEGRADATION_COST,
        CONF_ROUNDTRIP_EFFICIENCY,
        CONF_SAFETY_MARGIN,
        CONF_BATTERY_MIN_SOC,
        CONF_BATTERY_MAX_SOC,
        CONF_MAX_CHARGE_POWER_W,
        CONF_MAX_DISCHARGE_POWER_W,
        CONF_CONTROL_MODE,
        CONF_BATTERY_POWER_CONTROL_ENTITY,
        CONF_WRITE_THROTTLE_SECONDS,
        CONF_MIN_DWELL_SECONDS,
        CONF_HYSTERESIS_W,
        CONF_ENABLE_EV,
        CONF_EV_CURRENT_CONTROL_ENTITY,
        CONF_EV_MIN_CURRENT_A,
        CONF_EV_MAX_CURRENT_A,
        CONF_EV_PHASES,
        CONF_EV_TARGET_SOC,
        CONF_ENABLE_HEATPUMP,
        CONF_HEATPUMP_OFFSET_CONTROL_ENTITY,
        CONF_HEATPUMP_MAX_OFFSET,
    }
)

# Enum choices surfaced to the settings tab so it can render dropdowns.
_ENUMS: dict[str, list[str]] = {
    CONF_PRICE_INTERVAL: [INTERVAL_HOURLY, INTERVAL_QUARTERLY],
    CONF_REGULATION_PROFILE: [
        REGULATION_SALDERING,
        REGULATION_NO_SALDERING,
        REGULATION_CAPACITY,
    ],
    CONF_OPTIMIZER_MODE: [OPTIMIZER_HEURISTIC, OPTIMIZER_MILP],
    CONF_CONTROL_MODE: [CONTROL_OBSERVE, CONTROL_ACTIVE],
    CONF_IMBALANCE_UNIT: [IMBALANCE_UNIT_KWH, IMBALANCE_UNIT_MWH],
}

_KEY = f"{DOMAIN}_ws_registered"


def _loaded_entry(hass: HomeAssistant) -> KDBrainConfigEntry | None:
    """Return the single loaded KD Brain entry, if any."""
    entries = hass.config_entries.async_loaded_entries(DOMAIN)
    if not entries:
        return None
    return cast("KDBrainConfigEntry", entries[0])


def _round(value: float | None) -> float | None:
    return None if value is None else round(value, PRICE_PRECISION)


def _price_section(entry: KDBrainConfigEntry) -> dict[str, Any]:
    """Build the price part of the snapshot (today/tomorrow curves + stats)."""
    coordinator = entry.runtime_data.price_coordinator
    series = coordinator.data
    if series is None or series.is_empty:
        return {"available": False}

    tz = dt_util.DEFAULT_TIME_ZONE
    now = dt_util.utcnow()
    local = dt_util.now()
    today = series.slice_local_day(local.date(), tz)
    tomorrow = series.slice_local_day((local + timedelta(days=1)).date(), tz)
    interval = entry.options.get(CONF_PRICE_INTERVAL, DEFAULT_PRICE_INTERVAL)
    display = series.to_hourly() if interval == INTERVAL_HOURLY else series
    current = display.point_at(now)
    average = today.average_all_in()
    minimum = today.min_point()
    maximum = today.max_point()
    threshold = entry.options.get(
        CONF_PRICE_LOW_THRESHOLD, float(DEFAULT_PRICE_LOW_THRESHOLD)
    )

    return {
        "available": True,
        "interval": interval,
        "threshold": round(float(threshold), PRICE_PRECISION),
        "current_all_in": _round(float(current.all_in)) if current else None,
        "average_all_in": None if average is None else _round(float(average)),
        "min_all_in": _round(float(minimum.all_in)) if minimum else None,
        "max_all_in": _round(float(maximum.all_in)) if maximum else None,
        "today": today.as_dicts(),
        "tomorrow": tomorrow.as_dicts(),
        "today_hourly": today.to_hourly().as_dicts(),
        "tomorrow_hourly": tomorrow.to_hourly().as_dicts(),
    }


def _snapshot(entry: KDBrainConfigEntry) -> dict[str, Any]:
    """Assemble the full snapshot from the entry's coordinators."""
    runtime = entry.runtime_data
    telemetry = runtime.telemetry_coordinator.data
    decision = runtime.optimization_coordinator.data
    actuation = runtime.actuation_coordinator.data
    ev = runtime.ev_coordinator.data
    heatpump = runtime.heatpump_coordinator.data

    return {
        "ts": dt_util.utcnow().isoformat(),
        "prices": _price_section(entry),
        "telemetry": telemetry.as_dict() if telemetry is not None else None,
        "decision": decision.as_dict() if decision is not None else None,
        "actuation": actuation.as_dict() if actuation is not None else None,
        "forecast": runtime.optimization_coordinator.forecast.as_dict(),
        "ev": ev.as_dict() if ev is not None else None,
        "heatpump": heatpump.as_dict() if heatpump is not None else None,
        "active_control": runtime.actuation_coordinator.safety_config.is_active,
    }


@callback
def async_register_websocket_api(hass: HomeAssistant) -> None:
    """Register the KD Brain websocket commands (idempotent)."""
    if hass.data.get(_KEY):
        return
    websocket_api.async_register_command(hass, ws_snapshot)
    websocket_api.async_register_command(hass, ws_config_get)
    websocket_api.async_register_command(hass, ws_config_update)
    hass.data[_KEY] = True


@websocket_command({vol.Required("type"): "kd_brain/snapshot"})
@callback
def ws_snapshot(
    hass: HomeAssistant,
    connection: ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return the consolidated live snapshot."""
    entry = _loaded_entry(hass)
    if entry is None:
        connection.send_error(msg["id"], "not_loaded", "No loaded KD Brain entry")
        return
    connection.send_result(msg["id"], _snapshot(entry))


@websocket_command({vol.Required("type"): "kd_brain/config/get"})
@callback
def ws_config_get(
    hass: HomeAssistant,
    connection: ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return current options plus settings metadata (presets and enums)."""
    entry = _loaded_entry(hass)
    if entry is None:
        connection.send_error(msg["id"], "not_loaded", "No loaded KD Brain entry")
        return
    providers = [
        {
            "id": provider.id,
            "name": provider.name,
            "markup": float(provider.markup),
            "feed_in": float(provider.feed_in),
            "monthly_fee": float(provider.monthly_fee),
        }
        for provider in sorted(PROVIDERS.values(), key=lambda p: p.name.lower())
    ]
    providers.append({"id": MANUAL, "name": "Handmatig"})
    connection.send_result(
        msg["id"],
        {
            "options": dict(entry.options),
            "providers": providers,
            "enums": _ENUMS,
            "editable_keys": sorted(EDITABLE_OPTION_KEYS),
        },
    )


@websocket_command(
    {
        vol.Required("type"): "kd_brain/config/update",
        vol.Required("changes"): {str: object},
    }
)
@require_admin
@async_response
async def ws_config_update(
    hass: HomeAssistant,
    connection: ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Validate and persist a partial options change (admin only)."""
    entry = _loaded_entry(hass)
    if entry is None:
        connection.send_error(msg["id"], "not_loaded", "No loaded KD Brain entry")
        return

    changes: dict[str, Any] = msg["changes"]
    unknown = [key for key in changes if key not in EDITABLE_OPTION_KEYS]
    if unknown:
        connection.send_error(
            msg["id"], "invalid_keys", f"Unknown option keys: {', '.join(unknown)}"
        )
        return

    merged = {**entry.options, **changes}
    hass.config_entries.async_update_entry(entry, options=merged)
    connection.send_result(msg["id"], {"options": merged})
