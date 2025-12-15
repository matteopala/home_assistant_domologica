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

        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=self.scan_interval),
        )

        # Debounce: se arrivano molte richieste di refresh in poco tempo,
        # le raggruppa in una sola (evita tempeste di chiamate)
        self._debounced_refresh = Debouncer(
            hass,
            _LOGGER,
            cooldown=0.5,
            immediate=False,
            function=self.async_request_refresh,
        )

        # Task micro-turbo (lo cancelliamo e lo reiniziamo ad ogni comando)
        self._turbo_task: asyncio.Task | None = None

    async def async_schedule_refresh(self) -> None:
        """Refresh debounced standard (1 chiamata anche se richiesto più volte)."""
        await self._debounced_refresh.async_call()

    async def async_schedule_refresh_turbo(self) -> None:
        """
        Micro-turbo: refresh subito (debounced) + refresh extra a breve distanza.
        Utile dopo un comando per confermare velocemente lo stato reale.
        """
        # refresh “immediato” (debounced)
        await self.async_schedule_refresh()

        # se un altro comando arriva, resettiamo il turbo (niente accodamenti infiniti)
        if self._turbo_task and not self._turbo_task.done():
            self._turbo_task.cancel()

        self._turbo_task = asyncio.create_task(self._turbo_worker())

    async def _turbo_worker(self) -> None:
        try:
            # 2 refresh extra: +1s e +3s (puoi cambiare i tempi se vuoi)
            await asyncio.sleep(1.0)
            await self.async_schedule_refresh()

            await asyncio.sleep(2.0)  # totale ~3s dal comando
            await self.async_schedule_refresh()
        except asyncio.CancelledError:
            # normale: arriva un nuovo comando e resetta il turbo
            return

    def apply_optimistic(
        self,
        element_id: str,
        updates: dict[str, object],
        remove: set[str] | None = None,
    ) -> None:
        """Aggiorna subito la cache e notifica HA (aggiorna anche sensori)."""
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
            return parse_statuses(root)
        except Exception as err:
            raise UpdateFailed(f"Domologica update failed: {err}") from err
