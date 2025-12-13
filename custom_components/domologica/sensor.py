import logging
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_devices):
    """Setup dei sensori Domologica da un entry configurato."""
    coordinator = hass.data["domologica"]["coordinator"]

    devices = []
    # Creiamo un sensore per ogni elemento presente nei dati del coordinator
    for element_path, statuses in coordinator.data.items():
        devices.append(DomologicaSensor(coordinator, element_path, statuses))

    async_add_devices(devices)


class DomologicaSensor(Entity):
    """Rappresenta un singolo sensore Domologica."""

    def __init__(self, coordinator, element_path, statuses):
        """Inizializza il sensore."""
        self.coordinator = coordinator
        self.element_path = element_path
        self.statuses = statuses  # dizionario di status
        self._attr_name = f"Domologica {element_path}"
        self._attr_unique_id = f"domologica_{element_path}"

    @property
    def state(self):
        """Restituisce lo stato principale del sensore."""
        # Se ci sono status, prendiamo il primo come stato principale
        if self.statuses:
            first_status = next(iter(self.statuses.values()))
            return first_status
        return None

    @property
    def extra_state_attributes(self):
        """Espone tutti gli altri status come attributi."""
        return self.statuses

    async def async_update(self):
        """Richiede al coordinator di aggiornare i dati."""
        await self.coordinator.async_request_refresh()
