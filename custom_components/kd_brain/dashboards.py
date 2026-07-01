"""Auto-generated Lovelace dashboard builder.

Builds a plain dashboard config (views/cards) from the entities that are
actually registered for a KD Brain config entry, so the layout always matches
what the user has configured (no dead cards for unconfigured devices).
"""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

# (section title, unique-id suffixes to include, in display order)
_SECTIONS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "Prijzen",
        (
            "current_price",
            "current_market_price",
            "current_feed_in_price",
            "next_price",
            "min_price_today",
            "max_price_today",
            "average_price_today",
            "price_low",
        ),
    ),
    (
        "Telemetrie",
        (
            "grid_power",
            "pv_power",
            "load_power",
            "battery_soc",
            "battery_power",
            "imbalance_price",
            "heat_pump_power",
        ),
    ),
    (
        "Optimalisatie",
        (
            "recommended_action",
            "active_strategy",
            "pv_forecast_power",
            "pv_forecast_today",
        ),
    ),
    (
        "Sturing & veiligheid",
        ("last_actuation", "active_control", "safety_intervened"),
    ),
    ("EV laden", ("recommended_ev_current", "ev_connected")),
    ("Warmtepomp", ("recommended_heatpump_offset",)),
)

_PRICE_CURVE_KEY = "price_data"


def _entities_by_key(hass: HomeAssistant, entry_id: str) -> dict[str, str]:
    """Map each entity's unique-id suffix (after ``{entry_id}_``) to its id."""
    registry = er.async_get(hass)
    prefix = f"{entry_id}_"
    by_key: dict[str, str] = {}
    for entity in er.async_entries_for_config_entry(registry, entry_id):
        if entity.unique_id.startswith(prefix):
            by_key[entity.unique_id[len(prefix) :]] = entity.entity_id
    return by_key


def build_dashboard(hass: HomeAssistant, entry_id: str) -> dict[str, Any]:
    """Build a Lovelace dashboard config for one KD Brain config entry."""
    by_key = _entities_by_key(hass, entry_id)

    cards: list[dict[str, Any]] = []
    for title, keys in _SECTIONS:
        entity_ids = [by_key[key] for key in keys if key in by_key]
        if entity_ids:
            cards.append({"type": "entities", "title": title, "entities": entity_ids})

    if _PRICE_CURVE_KEY in by_key:
        cards.append(
            {
                "type": "history-graph",
                "title": "Prijscurve",
                "entities": [by_key[_PRICE_CURVE_KEY]],
            }
        )

    return {
        "title": "KD Brain",
        "views": [{"title": "KD Brain", "path": "kd_brain", "cards": cards}],
    }
