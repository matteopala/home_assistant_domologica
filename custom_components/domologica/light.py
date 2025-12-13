from homeassistant.components.light import LightEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]

    lights = []
    for elem_id, status in coordinator.data.items():
        # consideriamo come luce se contiene "isswitchedon" o "isswitchedoff"
        if "isswitchedon" in status or "isswitchedoff" in status:
            lights.append(DomologicaLight(coordinator, elem_id))

    async_add_entities(lights)

class DomologicaLight(LightEntity):
    """Rappresenta una luce Domologica."""

    def __init__(self, coordinator, element_id):
        self.coordinator = coordinator
        self.element_id = element_id

    @property
    def name(self):
        return f"Domologica Light {self.element_id}"

    @property
    def is_on(self):
        status = self.coordinator.data.get(self.element_id, {})
        if "isswitchedon" in status:
            return True
        if "isswitchedoff" in status:
            return False
        return False

    async def async_turn_on(self, **kwargs):
        # qui potresti inserire comando remoto verso Domologica
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        # qui potresti inserire comando remoto verso Domologica
        self.async_write_ha_state()

    async def async_update(self):
        await self.coordinator.async_request_refresh()
