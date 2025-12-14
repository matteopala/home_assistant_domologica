from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, CONF_BASE_URL, CONF_USERNAME, CONF_PASSWORD, CONF_SCAN_INTERVAL
from .utils import async_fetch_element_statuses


class DomologicaCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.entry = entry
        data = entry.data
        opts = entry.options

        self.base_url = (opts.get(CONF_BASE_URL) or data[CONF_BASE_URL]).rstrip("/")
        self.username = opts.get(CONF_USERNAME) or data.get(CONF_USERNAME) or None
        self.password = opts.get(CONF_PASSWORD) or data.get(CONF_PASSWORD) or None
        self.scan_interval = int(opts.get(CONF_SCAN_INTERVAL) or data.get(CONF_SCAN_INTERVAL) or DEFAULT_SCAN_INTERVAL)

        super().__init__(
            hass,
            logger=None,
            name=DOMAIN,
            update_interval=timedelta(seconds=self.scan_interval),
        )

    async def _async_update_data(self):
        try:
            return await async_fetch_element_statuses(
                self.hass,
                self.base_url,
                self.username,
                self.password,
            )
        except Exception as err:
            raise UpdateFailed(f"Domologica update failed: {err}") from err