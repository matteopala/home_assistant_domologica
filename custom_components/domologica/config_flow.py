from __future__ import annotations

from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_BASE_URL,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
)
from .utils import async_test_connection


def _schema_user(defaults: dict[str, Any] | None = None) -> vol.Schema:
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(CONF_BASE_URL, default=defaults.get(CONF_BASE_URL, "")): str,
            vol.Optional(CONF_USERNAME, default=defaults.get(CONF_USERNAME, "")): str,
            vol.Optional(CONF_PASSWORD, default=defaults.get(CONF_PASSWORD, "")): str,
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=defaults.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            ): vol.Coerce(int),
        }
    )


class DomologicaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            base_url = user_input[CONF_BASE_URL].rstrip("/")
            user_input[CONF_BASE_URL] = base_url

            ok = await async_test_connection(
                self.hass,
                base_url,
                user_input.get(CONF_USERNAME) or None,
                user_input.get(CONF_PASSWORD) or None,
            )
            if not ok:
                errors["base"] = "cannot_connect"
            else:
                # Unica entry per base_url
                await self.async_set_unique_id(base_url)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="Domologica", data=user_input)

        return self.async_show_form(step_id="user", data_schema=_schema_user(), errors=errors)

    async def async_step_import(self, user_input: dict[str, Any]) -> FlowResult:
        return await self.async_step_user(user_input)


class DomologicaOptionsFlow(config_entries.OptionsFlow):
    """Options flow semplice: cambia solo scan interval.
    (Base URL e credenziali le lasciamo nel setup iniziale per evitare confusione)
    """

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self.entry = entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = {**(self.entry.data or {}), **(self.entry.options or {})}
        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=current.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): vol.Coerce(int)
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)


async def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> DomologicaOptionsFlow:
    return DomologicaOptionsFlow(config_entry)
