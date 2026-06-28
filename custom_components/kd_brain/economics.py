"""Economic / tariff model for KD Brain.

Turns a raw day-ahead market price into the all-in consumption price and the
feed-in (teruglever) price, using fully configurable Dutch tariff components.
Nothing here is hardcoded into the decision logic — every component comes from
the config entry options.

The current model is intentionally simple and milestone-appropriate (M1). The
treatment of saldering / dynamic feed-in compensation is part of the regulation
layer and is refined in M5.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from .const import (
    CONF_ENERGY_TAX,
    CONF_FEED_IN_MARKUP,
    CONF_MONTHLY_FEE,
    CONF_SUPPLIER_MARKUP,
    CONF_VAT,
    DEFAULT_ENERGY_TAX,
    DEFAULT_FEED_IN_MARKUP,
    DEFAULT_MONTHLY_FEE,
    DEFAULT_SUPPLIER_MARKUP,
    DEFAULT_VAT,
)


def _to_decimal(value: Any, default: Decimal) -> Decimal:
    """Coerce a config value (float/str/Decimal) to Decimal, or fall back."""
    if value is None:
        return default
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


@dataclass(frozen=True, slots=True)
class TariffConfig:
    """Configurable Dutch tariff components (all values excl. VAT in €/kWh)."""

    energy_tax: Decimal
    supplier_markup: Decimal
    feed_in_markup: Decimal
    monthly_fee: Decimal
    vat: Decimal

    @classmethod
    def from_options(cls, options: dict[str, Any]) -> TariffConfig:
        """Build a tariff config from config entry options, applying defaults."""
        return cls(
            energy_tax=_to_decimal(options.get(CONF_ENERGY_TAX), DEFAULT_ENERGY_TAX),
            supplier_markup=_to_decimal(
                options.get(CONF_SUPPLIER_MARKUP), DEFAULT_SUPPLIER_MARKUP
            ),
            feed_in_markup=_to_decimal(
                options.get(CONF_FEED_IN_MARKUP), DEFAULT_FEED_IN_MARKUP
            ),
            monthly_fee=_to_decimal(options.get(CONF_MONTHLY_FEE), DEFAULT_MONTHLY_FEE),
            vat=_to_decimal(options.get(CONF_VAT), DEFAULT_VAT),
        )

    def consumption_price(self, market: Decimal) -> Decimal:
        """Return the all-in consumption price for a raw market price.

        ``(market + energy_tax + supplier_markup) * (1 + VAT)``
        """
        net = market + self.energy_tax + self.supplier_markup
        return net * (Decimal(1) + self.vat)

    def feed_in_price(self, market: Decimal) -> Decimal:
        """Return the feed-in (teruglever) price for a raw market price.

        ``(market - feed_in_markup) * (1 + VAT)``. The feed-in markup models the
        per-kWh teruglever cost some suppliers charge. Saldering netting is
        handled by the regulation layer in a later milestone.
        """
        net = market - self.feed_in_markup
        return net * (Decimal(1) + self.vat)
