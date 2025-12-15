from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    DEFAULT_SCAN_INTERVAL,
    CONF_BASE_URL,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_ALIASES,
    CONF_ENABLED_ELEMENTS,
)
from .utils import async_fetch_element_statuses, parse_statuses

_LOGGER = logging.getLogger(__name__)


class DomologicaCoordinator(DataUpdateCoordinator[dict[str, dict[str, object]]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.entry = entry
        data = entry.data or {}
        opts = entry.options or {}

        base_url = (opts.get(CONF_BASE_URL) or data.get(CONF_BASE_URL) or "").rstrip("/")
        if not base_url:
            raise ValueError("Domologica: base_url missing in config entry")

        self.base_url = base_url
        self.username = opts.get(CONF_USERNAME) or data.get(CONF_USERNAME)
        self.password = opts.get(CONF_PASSWORD) or data.get(CONF_PASSWORD)
        self.scan_interval = int(
            opts.get(CONF_SCAN_INTERVAL)
            or data.get(CONF_SCAN_INTERVAL)
            or DEFAULT_SCAN_INTERVAL
        )

        # Wizard/Options
        self.aliases: dict[str, str] = dict(opts.get(CONF_ALIASES) or {})
        self.enabled_elements: set[str] = set(opts.get(CONF_ENABLED_ELEMENTS) or [])

        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=self.scan_interval),
        )

        # Debounce un po’ più largo: evita refresh inutili su toggle rapidi
        self._debounced_refresh = Debouncer(
            hass,
            _LOGGER,
            cooldown=1.0,
            immediate=False,
            function=self.async_request_refresh,
        )

        self._turbo_task: asyncio.Task | None = None

    # -------------------------
    # Refresh: NON BLOCCANTI
    # -------------------------

    def schedule_refresh(self) -> None:
        """Chiede un refresh senza bloccare la service call."""
        self.hass.async_create_task(self._debounced_refresh.async_call())

    def schedule_refresh_turbo(self) -> None:
        """
        Micro-turbo: refresh debounced subito + extra refresh a +1s e +3s.
        Non blocca mai il comando.
        """
        self.schedule_refresh()

        if self._turbo_task and not self._turbo_task.done():
            self._turbo_task.cancel()

        self._turbo_task = self.hass.async_create_task(self._turbo_worker())

    async def _turbo_worker(self) -> None:
        try:
            await asyncio.sleep(1.0)
            await self._debounced_refresh.async_call()
            await asyncio.sleep(2.0)  # totale ~3s dal comando
            await self._debounced_refresh.async_call()
        except asyncio.CancelledError:
            return

    # -------------------------
    # Optimistic cache update
    # -------------------------

    def apply_optimistic(
        self,
        element_id: str,
        updates: dict[str, object],
        remove: set[str] | None = None,
    ) -> None:
        current = self.data or {}
        new_data: dict[str, dict[str, object]] = dict(current)
        elem = dict(new_data.get(element_id, {}))

        if remove:
            for k in remove:
                elem.pop(k, None)

        elem.update(updates)
        new_data[element_id] = elem
        self.async_set_updated_data(new_data)

    async def _async_update_data(self) -> dict[str, dict[str, object]]:
        try:
            root = await async_fetch_element_statuses(
                self.hass, self.base_url, self.username, self.password
            )
            data = parse_statuses(root)

            if not self.enabled_elements:
                self.enabled_elements = set(data.keys())

            return data
        except Exception as err:
            raise UpdateFailed(f"Domologica update failed: {err}") from err
