from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS, SERVICE_REFRESH, SERVICE_COMMAND, ATTR_ELEMENT_ID, ATTR_ACTION
from .coordinator import DomologicaCoordinator
from .utils import async_command


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = DomologicaCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def _svc_refresh(call):
        await coordinator.async_request_refresh()

    async def _svc_command(call):
        element_id = str(call.data[ATTR_ELEMENT_ID])
        action = str(call.data[ATTR_ACTION])
        await async_command(
            hass,
            coordinator.base_url,
            element_id,
            action,
            coordinator.username,
            coordinator.password,
        )
        await coordinator.async_request_refresh()

    hass.services.async_register(DOMAIN, SERVICE_REFRESH, _svc_refresh)
    hass.services.async_register(DOMAIN, SERVICE_COMMAND, _svc_command)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        # servizi rimangono se ci sono altre entry; per semplicità non li deregistriamo
    return unload_ok