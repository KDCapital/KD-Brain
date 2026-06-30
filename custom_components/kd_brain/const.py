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
CONF_REGULATION_PROFILE: Final = "regulation_profile"
CONF_VAT: Final = "vat"

# NL regulation profiles (affect how exported energy is valued).
REGULATION_SALDERING: Final = "saldering_2026"  # net metering: feed-in nets at all-in
REGULATION_NO_SALDERING: Final = "no_saldering_2027"  # market-based feed-in
REGULATION_CAPACITY: Final = "capacity_2029"  # + time-dependent grid tariffs
DEFAULT_REGULATION_PROFILE: Final = REGULATION_SALDERING
CONF_PRICE_LOW_THRESHOLD: Final = "price_low_threshold"
CONF_UPDATE_INTERVAL_MINUTES: Final = "update_interval_minutes"

# --- Telemetry (entity-adapter) keys --------------------------------------
CONF_GRID_POWER_ENTITY: Final = "grid_power_entity"
CONF_PV_POWER_ENTITY: Final = "pv_power_entity"
CONF_LOAD_POWER_ENTITY: Final = "load_power_entity"
CONF_BATTERY_SOC_ENTITIES: Final = "battery_soc_entities"
CONF_BATTERY_POWER_ENTITIES: Final = "battery_power_entities"
CONF_BATTERY_CAPACITY_WH: Final = "battery_capacity_wh"
CONF_IMBALANCE_PRICE_ENTITY: Final = "imbalance_price_entity"
CONF_IMBALANCE_UNIT: Final = "imbalance_unit"
CONF_PV_FORECAST_POWER_ENTITY: Final = "pv_forecast_power_entity"
CONF_PV_FORECAST_TODAY_ENTITY: Final = "pv_forecast_today_entity"

# Imbalance price unit of the source entity.
IMBALANCE_UNIT_KWH: Final = "eur_kwh"
IMBALANCE_UNIT_MWH: Final = "eur_mwh"
DEFAULT_IMBALANCE_UNIT: Final = IMBALANCE_UNIT_KWH

# --- Engine: strategies, economics & battery limits (M3) ------------------
CONF_OPTIMIZER_MODE: Final = "optimizer_mode"
CONF_ENABLE_SELF_CONSUMPTION: Final = "enable_self_consumption"
CONF_ENABLE_DYNAMIC_PRICING: Final = "enable_dynamic_pricing"
CONF_ENABLE_ARBITRAGE: Final = "enable_arbitrage"
CONF_ENABLE_PEAK_SHAVING: Final = "enable_peak_shaving"
CONF_ENABLE_BACKUP_RESERVE: Final = "enable_backup_reserve"
CONF_PEAK_SHAVE_IMPORT_W: Final = "peak_shave_import_w"
CONF_PEAK_SHAVE_EXPORT_W: Final = "peak_shave_export_w"
CONF_BACKUP_RESERVE_SOC: Final = "backup_reserve_soc"
CONF_DEGRADATION_COST: Final = "degradation_cost"
CONF_ROUNDTRIP_EFFICIENCY: Final = "roundtrip_efficiency"
CONF_SAFETY_MARGIN: Final = "safety_margin"
CONF_BATTERY_MIN_SOC: Final = "battery_min_soc"
CONF_BATTERY_MAX_SOC: Final = "battery_max_soc"
CONF_MAX_CHARGE_POWER_W: Final = "max_charge_power_w"
CONF_MAX_DISCHARGE_POWER_W: Final = "max_discharge_power_w"

# --- Control & safety (M4) -------------------------------------------------
CONF_CONTROL_MODE: Final = "control_mode"
CONF_BATTERY_POWER_CONTROL_ENTITY: Final = "battery_power_control_entity"
CONF_WRITE_THROTTLE_SECONDS: Final = "write_throttle_seconds"
CONF_MIN_DWELL_SECONDS: Final = "min_dwell_seconds"
CONF_HYSTERESIS_W: Final = "hysteresis_w"

# Control modes: observe-only recommends; active actually steers hardware.
CONTROL_OBSERVE: Final = "observe_only"
CONTROL_ACTIVE: Final = "active"

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

# Engine defaults (all configurable, nothing hardcoded in the logic).
# Optimizer mode: heuristic (default) or exact MILP (requires optional highspy).
OPTIMIZER_HEURISTIC: Final = "heuristic"
OPTIMIZER_MILP: Final = "milp"
DEFAULT_OPTIMIZER_MODE: Final = OPTIMIZER_HEURISTIC

DEFAULT_ENABLE_SELF_CONSUMPTION: Final = True
DEFAULT_ENABLE_DYNAMIC_PRICING: Final = True
DEFAULT_ENABLE_ARBITRAGE: Final = True
DEFAULT_ENABLE_PEAK_SHAVING: Final = False  # opt-in: needs grid thresholds
DEFAULT_ENABLE_BACKUP_RESERVE: Final = False
DEFAULT_PEAK_SHAVE_IMPORT_W: Final = 3000
DEFAULT_PEAK_SHAVE_EXPORT_W: Final = 3000
DEFAULT_BACKUP_RESERVE_SOC: Final = 20.0  # percent
DEFAULT_DEGRADATION_COST: Final = Decimal("0.05")  # €/kWh throughput
DEFAULT_ROUNDTRIP_EFFICIENCY: Final = Decimal("0.90")  # fraction 0-1
DEFAULT_SAFETY_MARGIN: Final = Decimal("0.02")  # €/kWh
DEFAULT_BATTERY_MIN_SOC: Final = 10.0  # percent
DEFAULT_BATTERY_MAX_SOC: Final = 95.0  # percent
DEFAULT_MAX_CHARGE_POWER_W: Final = 2500
DEFAULT_MAX_DISCHARGE_POWER_W: Final = 2500

# Control & safety defaults — observe-only until the user explicitly opts in.
DEFAULT_CONTROL_MODE: Final = CONTROL_OBSERVE
DEFAULT_WRITE_THROTTLE_SECONDS: Final = 60
DEFAULT_MIN_DWELL_SECONDS: Final = 300
DEFAULT_HYSTERESIS_W: Final = 100

MIN_UPDATE_INTERVAL_MINUTES: Final = 5
MAX_UPDATE_INTERVAL_MINUTES: Final = 360

# --- Behaviour -------------------------------------------------------------
# epexprijzen.nl always returns 15-minute (MTU) data; this is the native grid.
NATIVE_RESOLUTION: Final = timedelta(minutes=15)
HOUR_RESOLUTION: Final = timedelta(hours=1)

# Currency unit used for all price entities.
CURRENCY_PER_KWH: Final = "€/kWh"
PRICE_PRECISION: Final = 4  # decimal places for displayed prices

# --- System mode -----------------------------------------------------------
# KD Brain only observes/recommends until actuators land (M4).
SYSTEM_MODE_OBSERVE: Final = "observe_only"

# --- Diagnostics / events --------------------------------------------------
EVENT_PRICES_UPDATED: Final = "kd_brain_prices_updated"
EVENT_DECISION: Final = "kd_brain_decision"
EVENT_ACTUATION: Final = "kd_brain_actuation"

# --- Repairs issue identifiers --------------------------------------------
ISSUE_PRICE_SOURCE_UNAVAILABLE: Final = "price_source_unavailable"
ISSUE_MILP_UNAVAILABLE: Final = "milp_unavailable"
