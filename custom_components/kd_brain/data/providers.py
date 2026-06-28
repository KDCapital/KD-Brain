"""Curated Dutch dynamic-energy supplier presets.

These values pre-fill the tariff form so users can pick their supplier instead of
entering every number by hand. They are starting points only -- every value remains
editable in the options flow. Supplier markups change over time; this dataset is
refreshed per release.

Source: epexprijzen.nl (publicly listed supplier tariffs). Energy tax and VAT are
national values and are NOT part of these presets.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Final

PROVIDERS_SOURCE: Final = "epexprijzen.nl"
PROVIDERS_UPDATED: Final = "2026-06-28"

# Sentinel option for "enter my own values".
MANUAL: Final = "manual"


@dataclass(frozen=True, slots=True)
class Provider:
    """A Dutch dynamic-energy supplier with its tariff components."""

    id: str
    name: str
    markup: Decimal  # leveranciersopslag, excl. BTW (EUR/kWh)
    feed_in: Decimal  # terugleverkosten, excl. BTW (EUR/kWh); 0 if not published
    monthly_fee: Decimal  # vaste leveringskosten (EUR/maand)
    battery_control: bool  # supplier offers its own home-battery steering


PROVIDERS: Final[dict[str, Provider]] = {
    "anwb-energie": Provider(
        id="anwb-energie",
        name="ANWB Energie",
        markup=Decimal("0.01488"),
        feed_in=Decimal("0.00000"),
        monthly_fee=Decimal("8.50"),
        battery_control=False,
    ),
    "budget-energie": Provider(
        id="budget-energie",
        name="Budget Energie",
        markup=Decimal("0.01390"),
        feed_in=Decimal("0.00000"),
        monthly_fee=Decimal("5.99"),
        battery_control=False,
    ),
    "coolblue-energie": Provider(
        id="coolblue-energie",
        name="Coolblue Energie",
        markup=Decimal("0.01876"),
        feed_in=Decimal("0.00000"),
        monthly_fee=Decimal("6.20"),
        battery_control=False,
    ),
    "easyenergy": Provider(
        id="easyenergy",
        name="easyEnergy",
        markup=Decimal("0.01800"),
        feed_in=Decimal("0.00000"),
        monthly_fee=Decimal("7.00"),
        battery_control=False,
    ),
    "eneco": Provider(
        id="eneco",
        name="Eneco",
        markup=Decimal("0.01992"),
        feed_in=Decimal("0.00000"),
        monthly_fee=Decimal("7.00"),
        battery_control=False,
    ),
    "energie-vanons": Provider(
        id="energie-vanons",
        name="Energie VanOns",
        markup=Decimal("0.02397"),
        feed_in=Decimal("0.00000"),
        monthly_fee=Decimal("6.99"),
        battery_control=False,
    ),
    "energyzero": Provider(
        id="energyzero",
        name="EnergyZero",
        markup=Decimal("0.01851"),
        feed_in=Decimal("0.00000"),
        monthly_fee=Decimal("7.51"),
        battery_control=False,
    ),
    "engie": Provider(
        id="engie",
        name="Engie",
        markup=Decimal("0.01570"),
        feed_in=Decimal("0.00000"),
        monthly_fee=Decimal("6.95"),
        battery_control=False,
    ),
    "frank-energie": Provider(
        id="frank-energie",
        name="Frank Energie",
        markup=Decimal("0.01504"),
        feed_in=Decimal("0.01050"),
        monthly_fee=Decimal("7.00"),
        battery_control=True,
    ),
    "frank-energie-slim": Provider(
        id="frank-energie-slim",
        name="Frank Energie (met Slim terugleveren)",
        markup=Decimal("0.01504"),
        feed_in=Decimal("0.00000"),
        monthly_fee=Decimal("7.25"),
        battery_control=True,
    ),
    "hegg": Provider(
        id="hegg",
        name="Hegg",
        markup=Decimal("0.02800"),
        feed_in=Decimal("0.00000"),
        monthly_fee=Decimal("7.50"),
        battery_control=True,
    ),
    "innova": Provider(
        id="innova",
        name="Innova",
        markup=Decimal("0.02073"),
        feed_in=Decimal("0.02530"),
        monthly_fee=Decimal("6.58"),
        battery_control=False,
    ),
    "nextenergy": Provider(
        id="nextenergy",
        name="NextEnergy",
        markup=Decimal("0.01810"),
        feed_in=Decimal("0.01810"),
        monthly_fee=Decimal("5.99"),
        battery_control=True,
    ),
    "powerpeers": Provider(
        id="powerpeers",
        name="PowerPeers",
        markup=Decimal("0.00826"),
        feed_in=Decimal("0.00000"),
        monthly_fee=Decimal("6.25"),
        battery_control=True,
    ),
    "quatt-energy": Provider(
        id="quatt-energy",
        name="Quatt Energy",
        markup=Decimal("0.01500"),
        feed_in=Decimal("0.00000"),
        monthly_fee=Decimal("7.50"),
        battery_control=False,
    ),
    "samenom": Provider(
        id="samenom",
        name="SamenOm",
        markup=Decimal("0.02066"),
        feed_in=Decimal("0.02066"),
        monthly_fee=Decimal("8.57"),
        battery_control=False,
    ),
    "samsam": Provider(
        id="samsam",
        name="SamSam",
        markup=Decimal("0.01853"),
        feed_in=Decimal("0.00000"),
        monthly_fee=Decimal("7.99"),
        battery_control=False,
    ),
    "tibber": Provider(
        id="tibber",
        name="Tibber",
        markup=Decimal("0.02050"),
        feed_in=Decimal("0.02050"),
        monthly_fee=Decimal("5.99"),
        battery_control=True,
    ),
    "vandebron": Provider(
        id="vandebron",
        name="VandeBron",
        markup=Decimal("0.01653"),
        feed_in=Decimal("0.01810"),
        monthly_fee=Decimal("6.25"),
        battery_control=False,
    ),
    "vattenfall": Provider(
        id="vattenfall",
        name="Vattenfall",
        markup=Decimal("0.02107"),
        feed_in=Decimal("0.00000"),
        monthly_fee=Decimal("7.95"),
        battery_control=False,
    ),
    "zonneplan": Provider(
        id="zonneplan",
        name="Zonneplan",
        markup=Decimal("0.01653"),
        feed_in=Decimal("0.00000"),
        monthly_fee=Decimal("6.25"),
        battery_control=True,
    ),
}
