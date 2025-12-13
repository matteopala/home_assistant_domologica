from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN, PLATFORMS
from .coordinator import DomologicaDataUpdateCoordinator

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Setup della Domologica integration da Config Flow."""
    coordinator = DomologicaDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Forward setup per le piattaforme
    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setups(entry, [platform])
        )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload dell’integration."""
    unload_ok = all(
        await hass.config_entries.async_forward_entry_unload(entry, platform)
        for platform in PLATFORMS
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
