"""Config and options flow for KD Brain.

The flow lets users pick their energy supplier so the tariff components are
pre-filled from a curated dataset, while keeping every value editable. Choosing
"manual" (or simply editing the pre-filled values) gives full manual control.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from homeassistant.config_entries import (
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)
import voluptuous as vol

from .const import (
    CONF_BATTERY_CAPACITY_WH,
    CONF_BATTERY_POWER_ENTITIES,
    CONF_BATTERY_SOC_ENTITIES,
    CONF_ENERGY_TAX,
    CONF_FEED_IN_MARKUP,
    CONF_GRID_POWER_ENTITY,
    CONF_LOAD_POWER_ENTITY,
    CONF_MONTHLY_FEE,
    CONF_PRICE_INTERVAL,
    CONF_PRICE_LOW_THRESHOLD,
    CONF_PRICE_SOURCE,
    CONF_PV_POWER_ENTITY,
    CONF_SUPPLIER,
    CONF_SUPPLIER_MARKUP,
    CONF_UPDATE_INTERVAL_MINUTES,
    CONF_VAT,
    DEFAULT_BATTERY_CAPACITY_WH,
    DEFAULT_ENERGY_TAX,
    DEFAULT_FEED_IN_MARKUP,
    DEFAULT_MONTHLY_FEE,
    DEFAULT_PRICE_INTERVAL,
    DEFAULT_PRICE_LOW_THRESHOLD,
    DEFAULT_PRICE_SOURCE,
    DEFAULT_SUPPLIER_MARKUP,
    DEFAULT_UPDATE_INTERVAL_MINUTES,
    DEFAULT_VAT,
    DOMAIN,
    INTERVAL_HOURLY,
    INTERVAL_QUARTERLY,
    MAX_UPDATE_INTERVAL_MINUTES,
    MIN_UPDATE_INTERVAL_MINUTES,
    PRICE_SOURCE_EPEXPRIJZEN,
)
from .data.providers import MANUAL, PROVIDERS

# Telemetry option keys handled by the "devices" step.
_DEVICE_ENTITY_KEYS = (
    CONF_GRID_POWER_ENTITY,
    CONF_PV_POWER_ENTITY,
    CONF_LOAD_POWER_ENTITY,
    CONF_BATTERY_SOC_ENTITIES,
    CONF_BATTERY_POWER_ENTITIES,
)

TITLE = "KD Brain"

# Tariff/price values (everything except the supplier selection).
_DEFAULTS: dict[str, Any] = {
    CONF_PRICE_SOURCE: DEFAULT_PRICE_SOURCE,
    CONF_PRICE_INTERVAL: DEFAULT_PRICE_INTERVAL,
    CONF_ENERGY_TAX: float(DEFAULT_ENERGY_TAX),
    CONF_SUPPLIER_MARKUP: float(DEFAULT_SUPPLIER_MARKUP),
    CONF_FEED_IN_MARKUP: float(DEFAULT_FEED_IN_MARKUP),
    CONF_MONTHLY_FEE: float(DEFAULT_MONTHLY_FEE),
    CONF_VAT: float(DEFAULT_VAT),
    CONF_PRICE_LOW_THRESHOLD: float(DEFAULT_PRICE_LOW_THRESHOLD),
    CONF_UPDATE_INTERVAL_MINUTES: DEFAULT_UPDATE_INTERVAL_MINUTES,
}


def _supplier_options() -> list[SelectOptionDict]:
    """Build the supplier dropdown: known providers plus a manual option."""
    options = [
        SelectOptionDict(value=provider.id, label=provider.name)
        for provider in sorted(PROVIDERS.values(), key=lambda p: p.name.lower())
    ]
    options.append(
        SelectOptionDict(value=MANUAL, label="Anders / handmatig (enter manually)")
    )
    return options


def _supplier_schema(default: str) -> vol.Schema:
    """Build the schema for the single supplier-selection step."""
    return vol.Schema(
        {
            vol.Required(CONF_SUPPLIER, default=default): SelectSelector(
                SelectSelectorConfig(
                    options=_supplier_options(), mode=SelectSelectorMode.DROPDOWN
                )
            )
        }
    )


def _apply_provider(values: Mapping[str, Any], supplier: str) -> dict[str, Any]:
    """Return values with supplier-specific fields pre-filled from the dataset."""
    merged = {**_DEFAULTS, **{k: v for k, v in values.items() if k in _DEFAULTS}}
    provider = PROVIDERS.get(supplier)
    if provider is not None:
        merged[CONF_SUPPLIER_MARKUP] = float(provider.markup)
        merged[CONF_FEED_IN_MARKUP] = float(provider.feed_in)
        merged[CONF_MONTHLY_FEE] = float(provider.monthly_fee)
    return merged


def _price_per_kwh() -> NumberSelector:
    """Return a number selector for a €/kWh tariff component."""
    return NumberSelector(
        NumberSelectorConfig(
            min=-1,
            max=2,
            step="any",
            mode=NumberSelectorMode.BOX,
            unit_of_measurement="€/kWh",
        )
    )


def _values_schema(values: Mapping[str, Any]) -> vol.Schema:
    """Build the tariff/price values schema, pre-filled with ``values``."""

    def default(key: str) -> Any:
        return values.get(key, _DEFAULTS[key])

    return vol.Schema(
        {
            vol.Required(
                CONF_PRICE_SOURCE, default=default(CONF_PRICE_SOURCE)
            ): SelectSelector(
                SelectSelectorConfig(
                    options=[PRICE_SOURCE_EPEXPRIJZEN],
                    translation_key="price_source",
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(
                CONF_PRICE_INTERVAL, default=default(CONF_PRICE_INTERVAL)
            ): SelectSelector(
                SelectSelectorConfig(
                    options=[INTERVAL_HOURLY, INTERVAL_QUARTERLY],
                    translation_key="price_interval",
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(
                CONF_ENERGY_TAX, default=default(CONF_ENERGY_TAX)
            ): _price_per_kwh(),
            vol.Required(
                CONF_SUPPLIER_MARKUP, default=default(CONF_SUPPLIER_MARKUP)
            ): _price_per_kwh(),
            vol.Required(
                CONF_FEED_IN_MARKUP, default=default(CONF_FEED_IN_MARKUP)
            ): _price_per_kwh(),
            vol.Required(
                CONF_MONTHLY_FEE, default=default(CONF_MONTHLY_FEE)
            ): NumberSelector(
                NumberSelectorConfig(
                    min=0,
                    max=100,
                    step="any",
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement="€/maand",
                )
            ),
            vol.Required(CONF_VAT, default=default(CONF_VAT)): NumberSelector(
                NumberSelectorConfig(
                    min=0, max=1, step=0.01, mode=NumberSelectorMode.BOX
                )
            ),
            vol.Required(
                CONF_PRICE_LOW_THRESHOLD, default=default(CONF_PRICE_LOW_THRESHOLD)
            ): _price_per_kwh(),
            vol.Required(
                CONF_UPDATE_INTERVAL_MINUTES,
                default=default(CONF_UPDATE_INTERVAL_MINUTES),
            ): NumberSelector(
                NumberSelectorConfig(
                    min=MIN_UPDATE_INTERVAL_MINUTES,
                    max=MAX_UPDATE_INTERVAL_MINUTES,
                    step=5,
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement="min",
                )
            ),
        }
    )


def _power_entity() -> EntitySelector:
    """Return an entity selector for a power sensor."""
    return EntitySelector(EntitySelectorConfig(domain="sensor"))


def _power_entities() -> EntitySelector:
    """Return an entity selector for multiple sensors."""
    return EntitySelector(EntitySelectorConfig(domain="sensor", multiple=True))


def _devices_schema(values: Mapping[str, Any]) -> vol.Schema:
    """Build the telemetry/devices schema, pre-filled with ``values``."""

    def suggest(key: str) -> dict[str, Any]:
        return {"suggested_value": values.get(key)}

    return vol.Schema(
        {
            vol.Optional(
                CONF_GRID_POWER_ENTITY, description=suggest(CONF_GRID_POWER_ENTITY)
            ): _power_entity(),
            vol.Optional(
                CONF_PV_POWER_ENTITY, description=suggest(CONF_PV_POWER_ENTITY)
            ): _power_entity(),
            vol.Optional(
                CONF_LOAD_POWER_ENTITY, description=suggest(CONF_LOAD_POWER_ENTITY)
            ): _power_entity(),
            vol.Optional(
                CONF_BATTERY_SOC_ENTITIES,
                description=suggest(CONF_BATTERY_SOC_ENTITIES),
            ): _power_entities(),
            vol.Optional(
                CONF_BATTERY_POWER_ENTITIES,
                description=suggest(CONF_BATTERY_POWER_ENTITIES),
            ): _power_entities(),
            vol.Optional(
                CONF_BATTERY_CAPACITY_WH,
                default=values.get(
                    CONF_BATTERY_CAPACITY_WH, DEFAULT_BATTERY_CAPACITY_WH
                ),
            ): NumberSelector(
                NumberSelectorConfig(
                    min=500,
                    max=100000,
                    step=100,
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement="Wh",
                )
            ),
        }
    )


class KDBrainConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial setup of KD Brain."""

    VERSION = 1
    MINOR_VERSION = 1

    def __init__(self) -> None:
        """Initialise transient flow state."""
        self._supplier: str = MANUAL

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 1: choose the energy supplier (or manual)."""
        if user_input is not None:
            self._supplier = user_input[CONF_SUPPLIER]
            return await self.async_step_tariff()
        return self.async_show_form(
            step_id="user", data_schema=_supplier_schema(MANUAL)
        )

    async def async_step_tariff(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Step 2: confirm/adjust the (pre-filled) tariff values."""
        if user_input is not None:
            options = {CONF_SUPPLIER: self._supplier, **user_input}
            return self.async_create_entry(title=TITLE, data={}, options=options)
        defaults = _apply_provider(_DEFAULTS, self._supplier)
        return self.async_show_form(
            step_id="tariff", data_schema=_values_schema(defaults)
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: Any) -> KDBrainOptionsFlow:
        """Return the options flow handler."""
        return KDBrainOptionsFlow()


class KDBrainOptionsFlow(OptionsFlow):
    """Handle changes to KD Brain options after setup."""

    def __init__(self) -> None:
        """Initialise transient flow state."""
        self._supplier: str = MANUAL

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Offer a supplier preset, manual tariff editing, or device setup."""
        return self.async_show_menu(
            step_id="init", menu_options=["supplier", "manual", "devices"]
        )

    async def async_step_supplier(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Pick a supplier to pre-fill the tariff values."""
        if user_input is not None:
            self._supplier = user_input[CONF_SUPPLIER]
            return await self.async_step_values()
        current = self.config_entry.options.get(CONF_SUPPLIER, MANUAL)
        return self.async_show_form(
            step_id="supplier", data_schema=_supplier_schema(current)
        )

    async def async_step_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Edit the current tariff values directly."""
        self._supplier = self.config_entry.options.get(CONF_SUPPLIER, MANUAL)
        return await self.async_step_values(user_input)

    async def async_step_values(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm/adjust the tariff values and save."""
        if user_input is not None:
            saved = {
                **self.config_entry.options,
                CONF_SUPPLIER: self._supplier,
                **user_input,
            }
            return self.async_create_entry(title="", data=saved)

        current = self.config_entry.options
        if self._supplier in PROVIDERS:
            defaults = _apply_provider(current, self._supplier)
        else:
            defaults = {**_DEFAULTS, **current}
        return self.async_show_form(
            step_id="values", data_schema=_values_schema(defaults)
        )

    async def async_step_devices(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Map Home Assistant entities onto KD Brain telemetry."""
        if user_input is not None:
            saved = dict(self.config_entry.options)
            # Optional entity selectors omit cleared fields; store None so they
            # can actually be removed instead of keeping the old value.
            for key in _DEVICE_ENTITY_KEYS:
                saved[key] = user_input.get(key)
            saved[CONF_BATTERY_CAPACITY_WH] = user_input.get(
                CONF_BATTERY_CAPACITY_WH, DEFAULT_BATTERY_CAPACITY_WH
            )
            return self.async_create_entry(title="", data=saved)
        return self.async_show_form(
            step_id="devices",
            data_schema=_devices_schema(self.config_entry.options),
        )
