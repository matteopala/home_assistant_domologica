import logging
from homeassistant.helpers.entity import Entity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
):
    """Setup dei sensori Domologica da config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities = []

    for element_path, statuses in coordinator.data.items():
        entities.append(
            DomologicaSensor(coordinator, element_path)
        )

    async_add_entities(entities)


class DomologicaSensor(Entity):
    """Sensore Domologica per un singolo ElementPath."""

    def __init__(self, coordinator, element_path: str):
        self.coordinator = coordinator
        self.element_path = element_path

        self._attr_name = f"Domologica {element_path}"
        self._attr_unique_id = f"domologica_{element_path}"

    @property
    def state(self):
        """Stato principale del sensore."""
        data = self.coordinator.data.get(self.element_path)
        if not data:
            return None

        # prende il primo status (es: isswitchedon / isswitchedoff)
        return next(iter(data.values()))

    @property
    def extra_state_attributes(self):
        """Attributi extra (tutti gli status XML)."""
        return self.coordinator.data.get(self.element_path, {})

    async def async_update(self):
        """Richiede refresh al coordinator."""
        await self.coordinator.async_request_refresh()
