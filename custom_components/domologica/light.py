import logging
from homeassistant.components.light import LightEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
):
    """Setup delle luci Domologica."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities = []

    for element_path, statuses in coordinator.data.items():
        # creiamo solo luci con stato on/off
        if "isswitchedon" in statuses or "isswitchedoff" in statuses:
            entities.append(
                DomologicaLight(coordinator, element_path)
            )

    async_add_entities(entities)


class DomologicaLight(LightEntity):
    """Luce Domologica."""

    def __init__(self, coordinator, element_path: str):
        self.coordinator = coordinator
        self.element_path = element_path

        self._attr_name = f"Domologica Light {element_path}"
        self._attr_unique_id = f"domologica_light_{element_path}"

    @property
    def is_on(self) -> bool | None:
        """Ritorna True se la luce è accesa."""
        data = self.coordinator.data.get(self.element_path)

        if not data:
            return None

        return "isswitchedon" in data

    @property
    def extra_state_attributes(self):
        """Attributi extra dall'XML."""
        return self.coordinator.data.get(self.element_path, {})

    async def async_update(self):
        """Aggiorna via coordinator."""
        await self.coordinator.async_request_refresh()
