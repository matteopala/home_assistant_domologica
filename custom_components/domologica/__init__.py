import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .coordinator import DomologicaDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]  # aggiungi altre piattaforme se serve

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Setup dell'integrazione Domologica da una Config Entry."""

    url = entry.data.get("url")
    username = entry.data.get("username")
    password = entry.data.get("password")
    polling_interval = entry.data.get("polling_interval", 2)  # default 2 secondi

    coordinator = DomologicaDataUpdateCoordinator(
        hass=hass,
        url=url,
        username=username,
        password=password,
        update_interval=polling_interval,
        logger=_LOGGER
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault("domologica", {})
    hass.data["domologica"][entry.entry_id] = coordinator

    # Invia le piattaforme da caricare
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True
