"""Shared fixtures for KD Brain tests."""

from __future__ import annotations

from collections.abc import Generator
from copy import deepcopy
import sys
from typing import Any

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

if sys.platform == "win32":
    import asyncio

    # Use the Selector event loop on Windows so that aiodns works without the
    # optional `winloop` dependency that the Proactor loop would require.
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # The harness can still recreate the loop as a Proactor loop, on which
    # aiodns refuses to start. Tests never resolve real hosts (aiohttp is
    # mocked), so fall back to aiohttp's threaded resolver during construction.
    import aiohttp.connector
    import aiohttp.resolver

    aiohttp.connector.DefaultResolver = aiohttp.resolver.ThreadedResolver

    # The HA test harness blocks sockets and only allows unix socketpairs. On
    # Windows asyncio's event loop uses a localhost AF_INET self-pipe instead,
    # which the harness blocks, breaking every test at loop setup. Neutralise the
    # block on Windows only; CI runs on Linux where the harness configuration
    # works unchanged and real network isolation is preserved.
    import pytest_socket

    pytest_socket.disable_socket = lambda *args, **kwargs: None  # type: ignore[assignment]

from custom_components.kd_brain.const import (
    CONF_ENERGY_TAX,
    CONF_FEED_IN_MARKUP,
    CONF_MONTHLY_FEE,
    CONF_PRICE_INTERVAL,
    CONF_PRICE_LOW_THRESHOLD,
    CONF_PRICE_SOURCE,
    CONF_SUPPLIER,
    CONF_SUPPLIER_MARKUP,
    CONF_UPDATE_INTERVAL_MINUTES,
    CONF_VAT,
    DOMAIN,
    INTERVAL_QUARTERLY,
    PRICE_SOURCE_EPEXPRIJZEN,
)
from custom_components.kd_brain.data.providers import MANUAL
from custom_components.kd_brain.data.sources.epexprijzen import API_URL

# A deterministic payload: two hours of quarters on the "today" date plus one
# hour for "tomorrow". Prices are chosen so aggregations are easy to verify.
PRICE_PAYLOAD: dict[str, Any] = {
    "today": [
        {"date": "2026-06-28T10:00:00+02:00", "price": 0.10},
        {"date": "2026-06-28T10:15:00+02:00", "price": 0.12},
        {"date": "2026-06-28T10:30:00+02:00", "price": 0.14},
        {"date": "2026-06-28T10:45:00+02:00", "price": 0.16},
        {"date": "2026-06-28T11:00:00+02:00", "price": 0.20},
        {"date": "2026-06-28T11:15:00+02:00", "price": 0.22},
        {"date": "2026-06-28T11:30:00+02:00", "price": 0.24},
        {"date": "2026-06-28T11:45:00+02:00", "price": 0.26},
    ],
    "tomorrow": [
        {"date": "2026-06-29T10:00:00+02:00", "price": 0.05},
        {"date": "2026-06-29T10:15:00+02:00", "price": 0.05},
        {"date": "2026-06-29T10:30:00+02:00", "price": 0.05},
        {"date": "2026-06-29T10:45:00+02:00", "price": 0.05},
    ],
}

# The tariff/price values shown on the second flow step (everything but supplier).
VALUES: dict[str, Any] = {
    CONF_PRICE_SOURCE: PRICE_SOURCE_EPEXPRIJZEN,
    CONF_PRICE_INTERVAL: INTERVAL_QUARTERLY,
    CONF_ENERGY_TAX: 0.10,
    CONF_SUPPLIER_MARKUP: 0.02,
    CONF_FEED_IN_MARKUP: 0.0,
    CONF_MONTHLY_FEE: 6.0,
    CONF_VAT: 0.21,
    CONF_PRICE_LOW_THRESHOLD: 0.20,
    CONF_UPDATE_INTERVAL_MINUTES: 30,
}

# Full stored options = supplier choice + tariff values.
OPTIONS: dict[str, Any] = {CONF_SUPPLIER: MANUAL, **VALUES}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(
    enable_custom_integrations: Any,
) -> Generator[None]:
    """Enable loading of the custom integration in every test."""
    yield


@pytest.fixture
def price_payload() -> dict[str, Any]:
    """Return a fresh copy of the sample price payload."""
    return deepcopy(PRICE_PAYLOAD)


@pytest.fixture
def mock_epex(
    aioclient_mock: AiohttpClientMocker, price_payload: dict[str, Any]
) -> AiohttpClientMocker:
    """Mock the epexprijzen.nl API with the sample payload."""
    aioclient_mock.get(API_URL, json=price_payload)
    return aioclient_mock


@pytest.fixture
def mock_entry() -> MockConfigEntry:
    """Return a mock config entry for KD Brain."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="KD Brain",
        data={},
        options=deepcopy(OPTIONS),
    )
