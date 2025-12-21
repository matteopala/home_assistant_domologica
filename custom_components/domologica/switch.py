from homeassistant.components.switch import SwitchEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    d = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([DomoSwitch(d["coord"], d["hub"], info) for eid, info in d["hub"].devices.items() if "Socket" in info["classId"] or "Switch" in info["classId"]])

class DomoSwitch(SwitchEntity):
    def __init__(self, coord, hub, info):
        self.coord, self.hub, self._id, self._name = coord, hub, info["id"], info["name"]

    @property
    def name(self): return self._name
    @property
    def unique_id(self): return f"domo_sw_{self._id}"

    @property
    def is_on(self):
        st = self.coord.data.get(self._id, {})
        return "isswitchedon" in st

    async def async_turn_on(self, **kwargs):
        await self.hub.send_command(self._id, "switchon")
        await self.coord.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self.hub.send_command(self._id, "switchoff")
        await self.coord.async_request_refresh()