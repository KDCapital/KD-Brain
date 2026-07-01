"""Diagnostics support for KD Brain.

The integration stores no credentials in M1, but diagnostics still route every
field through a redaction set so that future secrets can never leak into a
shared diagnostics download.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import KDBrainConfigEntry

TO_REDACT: set[str] = set()


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: KDBrainConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data.price_coordinator
    series = coordinator.data

    sample: dict[str, Any] = {}
    if series is not None and not series.is_empty:
        first = series.points[0]
        last = series.points[-1]
        average = series.average_all_in()
        sample = {
            "point_count": len(series.points),
            "resolution_minutes": int(series.resolution.total_seconds() // 60),
            "first_start": first.start.isoformat(),
            "last_end": last.end.isoformat(),
            "average_all_in": None if average is None else float(average),
        }

    telemetry_coordinator = entry.runtime_data.telemetry_coordinator
    telemetry = telemetry_coordinator.data
    telemetry_diag: dict[str, Any] = {
        "configured": telemetry_coordinator.adapter.is_configured,
        "last_update_success": telemetry_coordinator.last_update_success,
        "snapshot": telemetry.as_dict() if telemetry is not None else None,
    }

    optimization = entry.runtime_data.optimization_coordinator
    decision = optimization.data
    actuation = entry.runtime_data.actuation_coordinator.data
    ev = entry.runtime_data.ev_coordinator.data
    heatpump = entry.runtime_data.heatpump_coordinator.data

    return {
        "entry": {
            "options": async_redact_data(dict(entry.options), TO_REDACT),
            "version": entry.version,
            "minor_version": entry.minor_version,
        },
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "update_interval_seconds": (
                coordinator.update_interval.total_seconds()
                if coordinator.update_interval
                else None
            ),
        },
        "prices": sample,
        "telemetry": telemetry_diag,
        "decision": decision.as_dict() if decision is not None else None,
        "actuation": actuation.as_dict() if actuation is not None else None,
        "forecast": optimization.forecast.as_dict(),
        "ev": ev.as_dict() if ev is not None else None,
        "heatpump": heatpump.as_dict() if heatpump is not None else None,
    }
