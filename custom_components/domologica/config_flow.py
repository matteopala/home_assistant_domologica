from __future__ import annotations

import asyncio
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    CONF_BASE_URL,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    CONF_ALIASES,
    CONF_ENABLED_ELEMENTS,
)
from .utils import async_test_connection, async_fetch_element_statuses, parse_statuses, async_command


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

    def __init__(self) -> None:
        self._cfg: dict[str, Any] = {}
        self._data: dict[str, dict[str, object]] = {}
        self._all: list[str] = []
        self._lights: list[str] = []
        self._switches: list[str] = []
        self._covers: list[str] = []
        self._aliases: dict[str, str] = {}
        self._test_result: str = ""

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

                # Discovery per wizard
                root = await async_fetch_element_statuses(
                    self.hass,
                    base_url,
                    user_input.get(CONF_USERNAME) or None,
                    user_input.get(CONF_PASSWORD) or None,
                )
                data = parse_statuses(root)

                self._cfg = user_input
                self._data = data
                self._all = sorted(data.keys())

                # euristiche (uguali alle piattaforme)
                self._lights = [
                    eid for eid, st in data.items()
                    if ("isswitchedon" in st or "isswitchedoff" in st or "getdimmer" in st or "pwmValue" in st)
                ]
                self._switches = [eid for eid, st in data.items() if ("statuson" in st or "statusoff" in st)]
                self._covers = [eid for eid, st in data.items() if ("up switched" in st or "down switched" in st)]

                return await self.async_step_devices()

        return self.async_show_form(step_id="user", data_schema=_schema_user(), errors=errors)

    def _schema_devices(self) -> vol.Schema:
        options = self._all or []
        default_test = (self._lights[0] if self._lights else (options[0] if options else ""))

        return vol.Schema(
            {
                vol.Optional("enabled", default=options): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=options,
                        multiple=True,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional("element", default=default_test): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=options,
                        multiple=False,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional("alias", default=""): str,
                vol.Optional("run_test", default=False): bool,
            }
        )

    async def async_step_devices(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        placeholders = {
            "lights": str(len(self._lights)),
            "switches": str(len(self._switches)),
            "covers": str(len(self._covers)),
            "test_result": self._test_result or "",
        }

        if user_input is not None:
            enabled_list: list[str] = user_input.get("enabled", self._all)
            element: str = user_input.get("element") or ""
            alias: str = (user_input.get("alias") or "").strip()
            run_test: bool = bool(user_input.get("run_test"))

            if element and alias:
                self._aliases[element] = alias

            if run_test and element:
                # test "sicuro": ON poi OFF (o open/close) per non lasciare cose accese
                try:
                    if element in self._covers:
                        await async_command(
                            self.hass,
                            self._cfg[CONF_BASE_URL],
                            element,
                            "turnup",
                            self._cfg.get(CONF_USERNAME) or None,
                            self._cfg.get(CONF_PASSWORD) or None,
                        )
                        await asyncio.sleep(1.0)
                        await async_command(
                            self.hass,
                            self._cfg[CONF_BASE_URL],
                            element,
                            "turndown",
                            self._cfg.get(CONF_USERNAME) or None,
                            self._cfg.get(CONF_PASSWORD) or None,
                        )
                        self._test_result = f"Test cover {element}: turnup → turndown (OK)"
                    else:
                        await async_command(
                            self.hass,
                            self._cfg[CONF_BASE_URL],
                            element,
                            "switchon",
                            self._cfg.get(CONF_USERNAME) or None,
                            self._cfg.get(CONF_PASSWORD) or None,
                        )
                        await asyncio.sleep(1.0)
                        await async_command(
                            self.hass,
                            self._cfg[CONF_BASE_URL],
                            element,
                            "switchoff",
                            self._cfg.get(CONF_USERNAME) or None,
                            self._cfg.get(CONF_PASSWORD) or None,
                        )
                        self._test_result = f"Test element {element}: switchon → switchoff (OK)"

                except Exception:
                    self._test_result = f"Test element {element}: FAILED"
                    errors["base"] = "cannot_execute"

                placeholders["test_result"] = self._test_result

                # Rimostra lo step per permettere altri rename/test.
                return self.async_show_form(
                    step_id="devices",
                    data_schema=self._schema_devices(),
                    errors=errors,
                    description_placeholders=placeholders,
                )

            # Finish: crea entry + salva options (enabled + aliases)
            return self.async_create_entry(
                title="Domologica",
                data=self._cfg,
                options={
                    CONF_ENABLED_ELEMENTS: enabled_list or self._all,
                    CONF_ALIASES: self._aliases,
                },
            )

        return self.async_show_form(
            step_id="devices",
            data_schema=self._schema_devices(),
            errors=errors,
            description_placeholders=placeholders,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return DomologicaOptionsFlow(config_entry)


class DomologicaOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self.entry = entry
        self._aliases: dict[str, str] = dict((entry.options.get(CONF_ALIASES) or {}))
        self._enabled: list[str] = list((entry.options.get(CONF_ENABLED_ELEMENTS) or []))
        self._all: list[str] = []

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        # per la lista, proviamo a usare l'ultima cache del coordinator se presente
        # altrimenti chiediamo "element" in dropdown vuoto non è il massimo,
        # ma di solito hai già dati dopo che l'integrazione è configurata.
        hass = self.hass
        coordinator = hass.data.get(DOMAIN, {}).get(self.entry.entry_id)
        if coordinator and coordinator.data:
            self._all = sorted(list(coordinator.data.keys()))
        else:
            self._all = sorted(list(self._enabled))  # fallback

        if not self._enabled:
            self._enabled = self._all

        if user_input is not None:
            enabled_list: list[str] = user_input.get("enabled", self._enabled)
            element: str = user_input.get("element") or ""
            alias: str = (user_input.get("alias") or "").strip()

            if element and alias:
                self._aliases[element] = alias

            return self.async_create_entry(
                title="",
                data={
                    CONF_ENABLED_ELEMENTS: enabled_list,
                    CONF_ALIASES: self._aliases,
                },
            )

        schema = vol.Schema(
            {
                vol.Optional("enabled", default=self._enabled): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=self._all,
                        multiple=True,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional("element", default=(self._all[0] if self._all else "")): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=self._all,
                        multiple=False,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional("alias", default=""): str,
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
