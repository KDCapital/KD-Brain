"""Tests for the supplier preset dataset and prefill helper."""

from __future__ import annotations

from decimal import Decimal

from custom_components.kd_brain.config_flow import _DEFAULTS, _apply_provider
from custom_components.kd_brain.const import (
    CONF_FEED_IN_MARKUP,
    CONF_MONTHLY_FEE,
    CONF_SUPPLIER_MARKUP,
)
from custom_components.kd_brain.data.providers import MANUAL, PROVIDERS, Provider


def test_dataset_is_sane() -> None:
    """Every provider has consistent, non-negative tariff data."""
    assert PROVIDERS
    assert MANUAL not in PROVIDERS
    for key, provider in PROVIDERS.items():
        assert isinstance(provider, Provider)
        assert provider.id == key
        assert provider.name
        assert provider.markup >= Decimal("0")
        assert provider.feed_in >= Decimal("0")
        assert provider.monthly_fee >= Decimal("0")


def test_apply_provider_prefills_known_supplier() -> None:
    """A known supplier overrides the markup/feed-in/monthly-fee defaults."""
    tibber = PROVIDERS["tibber"]
    result = _apply_provider(_DEFAULTS, "tibber")
    assert result[CONF_SUPPLIER_MARKUP] == float(tibber.markup)
    assert result[CONF_FEED_IN_MARKUP] == float(tibber.feed_in)
    assert result[CONF_MONTHLY_FEE] == float(tibber.monthly_fee)


def test_apply_provider_manual_keeps_defaults() -> None:
    """The manual sentinel leaves the provided values untouched."""
    result = _apply_provider(_DEFAULTS, MANUAL)
    assert result[CONF_SUPPLIER_MARKUP] == _DEFAULTS[CONF_SUPPLIER_MARKUP]
