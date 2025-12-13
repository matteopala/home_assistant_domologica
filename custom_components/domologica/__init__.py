import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .coordinator import DomologicaDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setup dell'integrazione Domologica da Config Entry."""

    hass.data.setdefault(DOMAIN, {})

    url = entry.data["url"]
    username = entry.data["username"]
    password = entry.data["password"]

    # polling configurabile (default 2 secondi)
    polling_interval = entry.options.get("polling_interval", 2)

    coordinator = DomologicaDataUpdateCoordinator(
        hass=hass,
        url=url,
        username=username,
        password=password,
        update_interval=polling_interval,
    )

    # primo fetch bloccante
    await coordinator.async_config_entry_first_refresh()

    # salva il coordinator in modo corretto
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator
    }

    # carica le piattaforme (sensor, light, ecc.)
    await hass.config_entries.async_forward_entry_setups(
        entry, PLATFORMS
    )

    return True
