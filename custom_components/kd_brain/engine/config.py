"""Configuration for the optimisation engine.

Holds the user-tunable strategy toggles, battery limits and the economic
parameters that gate arbitrage. None of these are hardcoded in the strategy or
optimiser logic -- they all come from the config entry options.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from ..const import (
    CONF_BACKUP_RESERVE_SOC,
    CONF_BATTERY_MAX_SOC,
    CONF_BATTERY_MIN_SOC,
    CONF_DEGRADATION_COST,
    CONF_ENABLE_ARBITRAGE,
    CONF_ENABLE_BACKUP_RESERVE,
    CONF_ENABLE_DYNAMIC_PRICING,
    CONF_ENABLE_PEAK_SHAVING,
    CONF_ENABLE_SELF_CONSUMPTION,
    CONF_MAX_CHARGE_POWER_W,
    CONF_MAX_DISCHARGE_POWER_W,
    CONF_OPTIMIZER_MODE,
    CONF_PEAK_SHAVE_EXPORT_W,
    CONF_PEAK_SHAVE_IMPORT_W,
    CONF_ROUNDTRIP_EFFICIENCY,
    CONF_SAFETY_MARGIN,
    DEFAULT_BACKUP_RESERVE_SOC,
    DEFAULT_BATTERY_MAX_SOC,
    DEFAULT_BATTERY_MIN_SOC,
    DEFAULT_DEGRADATION_COST,
    DEFAULT_ENABLE_ARBITRAGE,
    DEFAULT_ENABLE_BACKUP_RESERVE,
    DEFAULT_ENABLE_DYNAMIC_PRICING,
    DEFAULT_ENABLE_PEAK_SHAVING,
    DEFAULT_ENABLE_SELF_CONSUMPTION,
    DEFAULT_MAX_CHARGE_POWER_W,
    DEFAULT_MAX_DISCHARGE_POWER_W,
    DEFAULT_OPTIMIZER_MODE,
    DEFAULT_PEAK_SHAVE_EXPORT_W,
    DEFAULT_PEAK_SHAVE_IMPORT_W,
    DEFAULT_ROUNDTRIP_EFFICIENCY,
    DEFAULT_SAFETY_MARGIN,
)


def _decimal(value: Any, default: Decimal) -> Decimal:
    """Coerce a config value to Decimal, or fall back to ``default``."""
    if value is None:
        return default
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


@dataclass(frozen=True, slots=True)
class OptimizerConfig:
    """User-tunable engine configuration."""

    optimizer_mode: str
    self_consumption: bool
    dynamic_pricing: bool
    arbitrage: bool
    peak_shaving: bool
    backup_reserve: bool
    degradation_cost: Decimal
    roundtrip_efficiency: Decimal
    safety_margin: Decimal
    battery_min_soc: float
    battery_max_soc: float
    max_charge_w: int
    max_discharge_w: int
    peak_import_w: int
    peak_export_w: int
    backup_reserve_soc: float

    @classmethod
    def from_options(cls, options: dict[str, Any]) -> OptimizerConfig:
        """Build the engine config from config entry options."""
        return cls(
            optimizer_mode=options.get(CONF_OPTIMIZER_MODE, DEFAULT_OPTIMIZER_MODE),
            self_consumption=bool(
                options.get(
                    CONF_ENABLE_SELF_CONSUMPTION, DEFAULT_ENABLE_SELF_CONSUMPTION
                )
            ),
            dynamic_pricing=bool(
                options.get(CONF_ENABLE_DYNAMIC_PRICING, DEFAULT_ENABLE_DYNAMIC_PRICING)
            ),
            arbitrage=bool(
                options.get(CONF_ENABLE_ARBITRAGE, DEFAULT_ENABLE_ARBITRAGE)
            ),
            peak_shaving=bool(
                options.get(CONF_ENABLE_PEAK_SHAVING, DEFAULT_ENABLE_PEAK_SHAVING)
            ),
            backup_reserve=bool(
                options.get(CONF_ENABLE_BACKUP_RESERVE, DEFAULT_ENABLE_BACKUP_RESERVE)
            ),
            degradation_cost=_decimal(
                options.get(CONF_DEGRADATION_COST), DEFAULT_DEGRADATION_COST
            ),
            roundtrip_efficiency=_decimal(
                options.get(CONF_ROUNDTRIP_EFFICIENCY),
                DEFAULT_ROUNDTRIP_EFFICIENCY,
            ),
            safety_margin=_decimal(
                options.get(CONF_SAFETY_MARGIN), DEFAULT_SAFETY_MARGIN
            ),
            battery_min_soc=float(
                options.get(CONF_BATTERY_MIN_SOC, DEFAULT_BATTERY_MIN_SOC)
            ),
            battery_max_soc=float(
                options.get(CONF_BATTERY_MAX_SOC, DEFAULT_BATTERY_MAX_SOC)
            ),
            max_charge_w=int(
                options.get(CONF_MAX_CHARGE_POWER_W, DEFAULT_MAX_CHARGE_POWER_W)
            ),
            max_discharge_w=int(
                options.get(CONF_MAX_DISCHARGE_POWER_W, DEFAULT_MAX_DISCHARGE_POWER_W)
            ),
            peak_import_w=int(
                options.get(CONF_PEAK_SHAVE_IMPORT_W, DEFAULT_PEAK_SHAVE_IMPORT_W)
            ),
            peak_export_w=int(
                options.get(CONF_PEAK_SHAVE_EXPORT_W, DEFAULT_PEAK_SHAVE_EXPORT_W)
            ),
            backup_reserve_soc=float(
                options.get(CONF_BACKUP_RESERVE_SOC, DEFAULT_BACKUP_RESERVE_SOC)
            ),
        )

    def arbitrage_profit(self, buy: Decimal, sell: Decimal) -> Decimal:
        """Return the net profit per kWh of charging at ``buy`` and later using.

        Accounts for round-trip losses (you must store ``1/efficiency`` kWh to
        get 1 kWh back), battery degradation and a configurable safety margin::

            profit = sell - buy / efficiency - degradation - safety_margin
        """
        if self.roundtrip_efficiency <= 0:
            return Decimal("-1")
        return (
            sell
            - buy / self.roundtrip_efficiency
            - self.degradation_cost
            - self.safety_margin
        )

    def can_charge(self, soc: float | None) -> bool:
        """Return whether charging is allowed at the given SOC (unknown = yes)."""
        return soc is None or soc < self.battery_max_soc

    def can_discharge(self, soc: float | None) -> bool:
        """Return whether discharging is allowed at SOC (unknown = yes)."""
        return soc is None or soc > self.battery_min_soc
