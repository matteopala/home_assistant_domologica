from homeassistant.config_entries import ConfigEntry # pyright: ignore[reportMissingImports]
from homeassistant.core import HomeAssistant # pyright: ignore[reportMissingImports]
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator # pyright: ignore[reportMissingImports]
from .coordinator import DomologicaDataUpdateCoordinator
from .const import DOMAIN, PLATFORMS

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Domologica integration from a config entry."""
    url = entry.data["url"]
    username = entry.data["username"]
    password = entry.data["password"]
    polling_interval = entry.options.get("polling_interval", 2)  # default 2 sec

    coordinator = DomologicaDataUpdateCoordinator(
        hass, url=url, username=username, password=password, update_interval=polling_interval
    )
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a Domologica config entry."""
    for platform in PLATFORMS:
        await hass.config_entries.async_forward_entry_unload(entry, platform)
    hass.data[DOMAIN].pop(entry.entry_id)
    return True
