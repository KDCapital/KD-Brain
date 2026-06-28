"""epexprijzen.nl day-ahead price source.

API contract (verified):
    GET https://epexprijzen.nl/api/prices
    -> {"today": [...], "tomorrow": [...]}
    Each item: {"date": "2026-06-28T00:00:00+02:00", "price": 0.1452}

``price`` is the raw market price in EUR/kWh (excl. taxes). Data is always at
15-minute (MTU) resolution (96 points/day). ``tomorrow`` is empty until the
day-ahead auction is published (~13:00 CET) and populated afterwards. No
authentication is required.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from decimal import Decimal, InvalidOperation
import logging
from typing import Any

from aiohttp import ClientError, ClientSession
from homeassistant.util import dt as dt_util

from ...const import NATIVE_RESOLUTION, PRICE_SOURCE_EPEXPRIJZEN
from ...economics import TariffConfig
from ..models import PricePoint, PriceSeries
from .base import PriceSource, PriceSourceError

_LOGGER = logging.getLogger(__name__)

API_URL = "https://epexprijzen.nl/api/prices"
REQUEST_TIMEOUT = 30
USER_AGENT = (
    "KD-Brain Home Assistant integration (+https://github.com/KDCapital/KD-Brain)"
)


class EpexPrijzenSource(PriceSource):
    """Fetches NL day-ahead prices from epexprijzen.nl."""

    def __init__(self, session: ClientSession) -> None:
        """Initialise with a shared aiohttp session."""
        self._session = session

    @property
    def name(self) -> str:
        """Return the source identifier."""
        return PRICE_SOURCE_EPEXPRIJZEN

    async def async_fetch(self, now: datetime, tariff: TariffConfig) -> PriceSeries:
        """Fetch today's and tomorrow's prices and apply the tariff model."""
        payload = await self._async_request()

        raw: list[dict[str, Any]] = []
        for key in ("today", "tomorrow"):
            value = payload.get(key)
            if isinstance(value, list):
                raw.extend(value)

        if not raw:
            raise PriceSourceError("epexprijzen.nl returned no price data")

        points = self._parse_points(raw, tariff)
        if not points:
            raise PriceSourceError("epexprijzen.nl returned no valid price points")

        points.sort(key=lambda point: point.start)
        return PriceSeries(points=tuple(points), resolution=NATIVE_RESOLUTION)

    async def _async_request(self) -> dict[str, Any]:
        """Perform the HTTP request and return the decoded JSON object."""
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                response = await self._session.get(
                    API_URL, headers={"User-Agent": USER_AGENT}
                )
                response.raise_for_status()
                data: Any = await response.json(content_type=None)
        except (TimeoutError, ClientError) as err:
            raise PriceSourceError(f"epexprijzen.nl request failed: {err}") from err

        if not isinstance(data, dict):
            raise PriceSourceError("epexprijzen.nl returned an unexpected payload")
        return data

    @staticmethod
    def _parse_points(
        raw: list[dict[str, Any]], tariff: TariffConfig
    ) -> list[PricePoint]:
        """Convert raw API items into tariff-aware price points."""
        points: list[PricePoint] = []
        for item in raw:
            start = dt_util.parse_datetime(str(item.get("date", "")))
            if start is None:
                continue
            try:
                market = Decimal(str(item["price"]))
            except (KeyError, InvalidOperation):
                continue

            start_utc = dt_util.as_utc(start)
            points.append(
                PricePoint(
                    start=start_utc,
                    end=start_utc + NATIVE_RESOLUTION,
                    market=market,
                    all_in=tariff.consumption_price(market),
                    feed_in=tariff.feed_in_price(market),
                )
            )
        return points
