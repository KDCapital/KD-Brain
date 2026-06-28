"""Constants for the KD Brain integration."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "kd_brain"
MANUFACTURER: Final = "KD Capital"
MODEL: Final = "KD Brain HEMS"

# Platforms shipped in M1 (Foundation + prices). More are added in later milestones.
PLATFORMS: Final[list[Platform]] = [Platform.SENSOR, Platform.BINARY_SENSOR]

# --- Config / options keys -------------------------------------------------
CONF_SUPPLIER: Final = "supplier"
CONF_PRICE_SOURCE: Final = "price_source"
CONF_PRICE_INTERVAL: Final = "price_interval"  # display aggregation: hourly | quarterly
CONF_ENERGY_TAX: Final = "energy_tax"
CONF_SUPPLIER_MARKUP: Final = "supplier_markup"
CONF_FEED_IN_MARKUP: Final = "feed_in_markup"
CONF_MONTHLY_FEE: Final = "monthly_fee"
CONF_VAT: Final = "vat"
CONF_PRICE_LOW_THRESHOLD: Final = "price_low_threshold"
CONF_UPDATE_INTERVAL_MINUTES: Final = "update_interval_minutes"

# --- Telemetry (entity-adapter) keys --------------------------------------
CONF_GRID_POWER_ENTITY: Final = "grid_power_entity"
CONF_PV_POWER_ENTITY: Final = "pv_power_entity"
CONF_LOAD_POWER_ENTITY: Final = "load_power_entity"
CONF_BATTERY_SOC_ENTITIES: Final = "battery_soc_entities"
CONF_BATTERY_POWER_ENTITIES: Final = "battery_power_entities"
CONF_BATTERY_CAPACITY_WH: Final = "battery_capacity_wh"

# --- Price source identifiers ---------------------------------------------
PRICE_SOURCE_EPEXPRIJZEN: Final = "epexprijzen"

# --- Price interval values -------------------------------------------------
INTERVAL_HOURLY: Final = "hourly"
INTERVAL_QUARTERLY: Final = "quarterly"

# --- Defaults --------------------------------------------------------------
# These are sensible starting points for the Netherlands; every value is fully
# configurable through the options flow and nothing is hardcoded in the logic.
DEFAULT_PRICE_SOURCE: Final = PRICE_SOURCE_EPEXPRIJZEN
DEFAULT_PRICE_INTERVAL: Final = INTERVAL_HOURLY
DEFAULT_ENERGY_TAX: Final = Decimal("0.1088")  # energiebelasting €/kWh (excl. BTW)
DEFAULT_SUPPLIER_MARKUP: Final = Decimal("0.02")  # leveranciersopslag €/kWh (excl. BTW)
DEFAULT_FEED_IN_MARKUP: Final = Decimal("0")  # terugleverkosten €/kWh (excl. BTW)
DEFAULT_MONTHLY_FEE: Final = Decimal("6.00")  # vaste leveringskosten €/maand
DEFAULT_VAT: Final = Decimal("0.21")  # BTW fraction
DEFAULT_PRICE_LOW_THRESHOLD: Final = Decimal("0.20")  # all-in €/kWh
DEFAULT_UPDATE_INTERVAL_MINUTES: Final = 30
DEFAULT_BATTERY_CAPACITY_WH: Final = 5000  # per battery (Marstek 5 kWh)

MIN_UPDATE_INTERVAL_MINUTES: Final = 5
MAX_UPDATE_INTERVAL_MINUTES: Final = 360

# --- Behaviour -------------------------------------------------------------
# epexprijzen.nl always returns 15-minute (MTU) data; this is the native grid.
NATIVE_RESOLUTION: Final = timedelta(minutes=15)
HOUR_RESOLUTION: Final = timedelta(hours=1)

# Currency unit used for all price entities.
CURRENCY_PER_KWH: Final = "€/kWh"
PRICE_PRECISION: Final = 4  # decimal places for displayed prices

# --- Diagnostics / events --------------------------------------------------
EVENT_PRICES_UPDATED: Final = "kd_brain_prices_updated"

# --- Repairs issue identifiers --------------------------------------------
ISSUE_PRICE_SOURCE_UNAVAILABLE: Final = "price_source_unavailable"
