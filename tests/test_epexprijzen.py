"""Tests for the epexprijzen.nl price source."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util
import pytest
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.kd_brain.const import REGULATION_NO_SALDERING
from custom_components.kd_brain.data.sources.base import PriceSourceError
from custom_components.kd_brain.data.sources.epexprijzen import (
    API_URL,
    EpexPrijzenSource,
)
from custom_components.kd_brain.economics import TariffConfig


def _tariff() -> TariffConfig:
    return TariffConfig(
        energy_tax=Decimal("0.10"),
        supplier_markup=Decimal("0.02"),
        feed_in_markup=Decimal("0"),
        monthly_fee=Decimal("6.00"),
        vat=Decimal("0.21"),
        regulation=REGULATION_NO_SALDERING,
    )


async def test_fetch_parses_payload(
    hass: HomeAssistant, mock_epex: AiohttpClientMocker
) -> None:
    """A valid payload yields a sorted, tariff-aware 15-minute series."""
    source = EpexPrijzenSource(async_get_clientsession(hass))
    series = await source.async_fetch(dt_util.utcnow(), _tariff())

    assert len(series.points) == 12  # 8 today + 4 tomorrow
    assert series.resolution == timedelta(minutes=15)

    first = series.points[0]
    assert first.market == Decimal("0.10")
    # (0.10 + 0.10 + 0.02) * 1.21 = 0.2662
    assert first.all_in == Decimal("0.2662")
    assert first.end - first.start == timedelta(minutes=15)

    # Points are sorted ascending by start time.
    starts = [point.start for point in series.points]
    assert starts == sorted(starts)


async def test_fetch_raises_on_http_error(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """An HTTP error is surfaced as PriceSourceError."""
    aioclient_mock.get(API_URL, status=500)
    source = EpexPrijzenSource(async_get_clientsession(hass))
    with pytest.raises(PriceSourceError):
        await source.async_fetch(dt_util.utcnow(), _tariff())


async def test_fetch_raises_on_empty_payload(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Empty data is treated as a failure rather than silent success."""
    aioclient_mock.get(API_URL, json={"today": [], "tomorrow": []})
    source = EpexPrijzenSource(async_get_clientsession(hass))
    with pytest.raises(PriceSourceError):
        await source.async_fetch(dt_util.utcnow(), _tariff())


async def test_fetch_skips_malformed_points(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Malformed entries are skipped without failing the whole fetch."""
    aioclient_mock.get(
        API_URL,
        json={
            "today": [
                {"date": "not-a-date", "price": 0.1},
                {"date": "2026-06-28T10:00:00+02:00"},
                {"date": "2026-06-28T10:15:00+02:00", "price": 0.12},
            ],
            "tomorrow": [],
        },
    )
    source = EpexPrijzenSource(async_get_clientsession(hass))
    series = await source.async_fetch(dt_util.utcnow(), _tariff())
    assert len(series.points) == 1
    assert series.points[0].market == Decimal("0.12")
