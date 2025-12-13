from homeassistant.components.light import LightEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .coordinator import DomologicaCoordinator
from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
session = async_get_clientsession(hass)
coordinator = DomologicaCoordinator(hass, session, entry.data)
await coordinator.async_config_entry_first_refresh()

lights = []
for element_id, info in coordinator.data.items():
if info.get("on") is not None:
lights.append(DomologicaLight(coordinator, element_id))

async_add_entities(lights)

class DomologicaLight(CoordinatorEntity, LightEntity):
def __init__(self, coordinator, element_id):
super().__init__(coordinator)
self._element_id = element_id
self._attr_unique_id = f"domologica_light_{element_id}"
self._attr_name = f"Domologica {element_id}"

@property
def is_on(self):
return self.coordinator.data[self._element_id]["on"]

@property
def available(self):
return self.coordinator.data.get(self._element_id) is not None