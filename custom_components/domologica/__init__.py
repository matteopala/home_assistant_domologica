import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .coordinator import DomologicaCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["light"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Domologica from a config entry."""
    xml_path = entry.data.get("xml_path", "/config/domologica_data.xml")
    
    coordinator = DomologicaCoordinator(hass, xml_path)
    await coordinator.async_config_entry_first_refresh()
    
    hass.data.setdefault("domologica", {})[entry.entry_id] = coordinator

    # Forward setup to platforms
    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload Domologica entry."""
    unload_ok = all(
        await hass.config_entries.async_forward_entry_unload(entry, platform)
        for platform in PLATFORMS
    )
    if unload_ok:
        hass.data["domologica"].pop(entry.entry_id)
    return unload_ok
