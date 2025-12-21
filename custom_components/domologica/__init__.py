import logging
from datetime import timedelta
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .const import DOMAIN, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
from .hub import DomologicaHub

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry):
    # Recupera i parametri inseriti dall'utente nella UI
    host = entry.data[CONF_HOST]
    user = entry.data[CONF_USERNAME]
    pwd = entry.data[CONF_PASSWORD]
    
    # Gestione polling (priorità alle opzioni modificate dopo il setup)
    scan_int = entry.options.get(
        CONF_SCAN_INTERVAL, 
        entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    )

    # Inizializza l'Hub con i parametri utente
    hub = DomologicaHub(host, user, pwd)
    await hub.async_discover()

    async def _update(): return await hub.get_all_statuses()
    
    coord = DataUpdateCoordinator(
        hass, 
        _LOGGER, 
        name=DOMAIN, 
        update_method=_update, 
        update_interval=timedelta(seconds=scan_int)
    )
    
    await coord.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {"hub": hub, "coord": coord}
    
    # Carica le piattaforme (Luci, Switch, Cover, Clima)
    await hass.config_entries.async_forward_entry_setups(entry, ["light", "switch", "cover", "sensor", "climate"])
    
    # Ascolta eventuali modifiche alle opzioni (polling)
    entry.add_update_listener(async_reload_entry)
    return True

async def async_reload_entry(hass, entry):
    """Ricarica l'integrazione se le opzioni cambiano."""
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass, entry):
    """Spegne correttamente l'integrazione."""
    return await hass.config_entries.async_unload_platforms(entry, ["light", "switch", "cover", "climate"])