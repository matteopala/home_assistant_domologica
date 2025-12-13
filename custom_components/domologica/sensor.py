from homeassistant.helpers.entity import Entity

async def async_setup_entry(hass, entry, async_add_devices):
    """Setup dei sensori da un entry configurato."""
    coordinator = hass.data["domologica"]["coordinator"]

    devices = []
    # Creiamo un sensore per ogni elemento, solo come esempio
    for element_path in coordinator.data.keys():
        devices.append(DomologicaSensor(coordinator, element_path))

    async_add_devices(devices)

class DomologicaSensor(Entity):
    """Rappresenta un singolo sensore Domologica."""

    def __init__(self, coordinator, element_path):
        self.coordinator = coordinator
        self.element_path = element_path
        self._attr_name = f"Domologica {element_path}"
        self._attr_unique_id = f"domologica_{element_path}"

    @property
    def state(self):
        """Restituisce lo stato del sensore."""
        data = self.coordinator.data.get(self.element_path)
        if not data:
            return None
        # Ad esempio, restituiamo il primo status disponibile
        return list(data.values())[0] if data else None

    async def async_update(self):
        """Chiedi al coordinator di aggiornare i dati."""
        await self.coordinator.async_request_refresh()
