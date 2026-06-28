"""Config and options flow for KD Brain."""

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
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)
import voluptuous as vol

from .const import (
    CONF_ENERGY_TAX,
    CONF_FEED_IN_MARKUP,
    CONF_PRICE_INTERVAL,
    CONF_PRICE_LOW_THRESHOLD,
    CONF_PRICE_SOURCE,
    CONF_SUPPLIER_MARKUP,
    CONF_UPDATE_INTERVAL_MINUTES,
    CONF_VAT,
    DEFAULT_ENERGY_TAX,
    DEFAULT_FEED_IN_MARKUP,
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

TITLE = "KD Brain"

_DEFAULTS: dict[str, Any] = {
    CONF_PRICE_SOURCE: DEFAULT_PRICE_SOURCE,
    CONF_PRICE_INTERVAL: DEFAULT_PRICE_INTERVAL,
    CONF_ENERGY_TAX: float(DEFAULT_ENERGY_TAX),
    CONF_SUPPLIER_MARKUP: float(DEFAULT_SUPPLIER_MARKUP),
    CONF_FEED_IN_MARKUP: float(DEFAULT_FEED_IN_MARKUP),
    CONF_VAT: float(DEFAULT_VAT),
    CONF_PRICE_LOW_THRESHOLD: float(DEFAULT_PRICE_LOW_THRESHOLD),
    CONF_UPDATE_INTERVAL_MINUTES: DEFAULT_UPDATE_INTERVAL_MINUTES,
}


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


def _build_schema(values: Mapping[str, Any]) -> vol.Schema:
    """Build the shared options schema, pre-filled with ``values``."""

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


class KDBrainConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial setup of KD Brain."""

    VERSION = 1
    MINOR_VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial configuration step."""
        if user_input is not None:
            return self.async_create_entry(title=TITLE, data={}, options=user_input)
        return self.async_show_form(
            step_id="user", data_schema=_build_schema(_DEFAULTS)
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: Any) -> KDBrainOptionsFlow:
        """Return the options flow handler."""
        return KDBrainOptionsFlow()


class KDBrainOptionsFlow(OptionsFlow):
    """Handle changes to KD Brain options after setup."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the tariff and price options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=_build_schema(self.config_entry.options),
        )
