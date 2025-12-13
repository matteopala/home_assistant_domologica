import logging

from homeassistant.components.light import LightEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry

from .coordinator import DomologicaCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up Domologica lights."""
    coordinator: DomologicaCoordinator = hass.data["domologica"][entry.entry_id]
    
    lights = []
    for path, statuses in coordinator.data.items():
        if "isswitchedon" in statuses or "isswitchedoff" in statuses:
            lights.append(DomologicaLight(coordinator, path))

    async_add_entities(lights)

class DomologicaLight(LightEntity):
    """Representation of a Domologica light."""

    def __init__(self, coordinator: DomologicaCoordinator, element_path: str):
        self.coordinator = coordinator
        self._element_path = element_path
        self._attr_name = f"Light {element_path}"
        self._attr_unique_id = f"domologica_light_{element_path}"
        self._is_on = False

    @property
    def is_on(self):
        return self._is_on

    async def async_update(self):
        """Update light status from coordinator data."""
        await self.coordinator.async_request_refresh()
        statuses = self.coordinator.data.get(self._element_path, {})
        if "isswitchedon" in statuses:
            self._is_on = True
        elif "isswitchedoff" in statuses:
            self._is_on = False

    async def async_turn_on(self, **kwargs):
        """Domologica lights are read-only in this example."""
        _LOGGER.debug("Turn on command ignored (read-only)")

    async def async_turn_off(self, **kwargs):
        """Domologica lights are read-only in this example."""
        _LOGGER.debug("Turn off command ignored (read-only)")
