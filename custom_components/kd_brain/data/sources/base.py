"""Price source protocol and shared errors.

A price source is a plug-in: implement :class:`PriceSource` and register it to
add support for a new provider, without touching the engine or coordinator.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from ...economics import TariffConfig
from ..models import PriceSeries


class PriceSourceError(Exception):
    """Raised when a price source cannot deliver valid data."""


@runtime_checkable
class PriceSource(Protocol):
    """Interface that every price provider implements."""

    @property
    def name(self) -> str:
        """Stable identifier for the source (matches a config value)."""

    async def async_fetch(self, now: datetime, tariff: TariffConfig) -> PriceSeries:
        """Fetch the latest available prices and apply the tariff model.

        Implementations must raise :class:`PriceSourceError` on any failure
        (network, parsing, validation) rather than returning partial data.
        """
