from __future__ import annotations

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

        # Debounce refresh post-comando: evita refresh "a raffica"
        self._debounced_refresh = Debouncer(
            hass,
            _LOGGER,
            cooldown=0.5,
            immediate=False,
            function=self.async_request_refresh,
        )

    async def async_schedule_refresh(self) -> None:
        await self._debounced_refresh.async_call()

    async def _async_update_data(self) -> dict[str, dict[str, object]]:
        try:
            root = await async_fetch_element_statuses(
                self.hass, self.base_url, self.username, self.password
            )
            return parse_statuses(root)
        except Exception as err:
            raise UpdateFailed(f"Domologica update failed: {err}") from err
