"""Unit tests for the tariff/economic model."""

from __future__ import annotations

from decimal import Decimal

from custom_components.kd_brain.const import (
    CONF_ENERGY_TAX,
    CONF_FEED_IN_MARKUP,
    CONF_SUPPLIER_MARKUP,
    CONF_VAT,
    DEFAULT_REGULATION_PROFILE,
    DEFAULT_VAT,
    REGULATION_NO_SALDERING,
    REGULATION_SALDERING,
)
from custom_components.kd_brain.economics import TariffConfig


def _tariff(
    feed_in_markup: str = "0", regulation: str = REGULATION_NO_SALDERING
) -> TariffConfig:
    return TariffConfig(
        energy_tax=Decimal("0.10"),
        supplier_markup=Decimal("0.02"),
        feed_in_markup=Decimal(feed_in_markup),
        monthly_fee=Decimal("6.00"),
        vat=Decimal("0.21"),
        regulation=regulation,
    )


def test_consumption_price() -> None:
    # (0.14 + 0.10 + 0.02) * 1.21 = 0.3146
    assert _tariff().consumption_price(Decimal("0.14")) == Decimal("0.3146")


def test_feed_in_price_market_based_without_saldering() -> None:
    # (0.20 - 0.01) * 1.21 = 0.2299
    tariff = _tariff(feed_in_markup="0.01", regulation=REGULATION_NO_SALDERING)
    assert tariff.feed_in_price(Decimal("0.20")) == Decimal("0.2299")


def test_feed_in_price_nets_at_all_in_under_saldering() -> None:
    # Under saldering, feed-in is worth the full all-in consumption price.
    tariff = _tariff(regulation=REGULATION_SALDERING)
    assert tariff.feed_in_price(Decimal("0.14")) == tariff.consumption_price(
        Decimal("0.14")
    )


def test_from_options_applies_defaults() -> None:
    tariff = TariffConfig.from_options({})
    assert tariff.vat == DEFAULT_VAT
    assert tariff.regulation == DEFAULT_REGULATION_PROFILE


def test_from_options_coerces_floats() -> None:
    tariff = TariffConfig.from_options(
        {
            CONF_ENERGY_TAX: 0.1088,
            CONF_SUPPLIER_MARKUP: 0.02,
            CONF_FEED_IN_MARKUP: 0.0,
            CONF_VAT: 0.21,
        }
    )
    assert tariff.energy_tax == Decimal("0.1088")
    assert isinstance(tariff.energy_tax, Decimal)
