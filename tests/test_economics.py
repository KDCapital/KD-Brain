"""Unit tests for the tariff/economic model."""

from __future__ import annotations

from decimal import Decimal

from custom_components.kd_brain.const import (
    CONF_ENERGY_TAX,
    CONF_FEED_IN_MARKUP,
    CONF_SUPPLIER_MARKUP,
    CONF_VAT,
    DEFAULT_VAT,
)
from custom_components.kd_brain.economics import TariffConfig


def _tariff() -> TariffConfig:
    return TariffConfig(
        energy_tax=Decimal("0.10"),
        supplier_markup=Decimal("0.02"),
        feed_in_markup=Decimal("0"),
        monthly_fee=Decimal("6.00"),
        vat=Decimal("0.21"),
    )


def test_consumption_price() -> None:
    # (0.14 + 0.10 + 0.02) * 1.21 = 0.3146
    assert _tariff().consumption_price(Decimal("0.14")) == Decimal("0.3146")


def test_feed_in_price() -> None:
    tariff = TariffConfig(
        energy_tax=Decimal("0.10"),
        supplier_markup=Decimal("0.02"),
        feed_in_markup=Decimal("0.01"),
        monthly_fee=Decimal("6.00"),
        vat=Decimal("0.21"),
    )
    # (0.20 - 0.01) * 1.21 = 0.2299
    assert tariff.feed_in_price(Decimal("0.20")) == Decimal("0.2299")


def test_from_options_applies_defaults() -> None:
    tariff = TariffConfig.from_options({})
    assert tariff.vat == DEFAULT_VAT


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
