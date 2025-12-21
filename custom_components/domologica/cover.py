from homeassistant.components.cover import CoverEntity, CoverDeviceClass
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    d = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([DomoCover(d["coord"], d["hub"], info) for eid, info in d["hub"].devices.items() if "Shutter" in info["classId"]])

class DomoCover(CoverEntity):
    def __init__(self, coord, hub, info):
        self.coord, self.hub, self._id, self._name = coord, hub, info["id"], info["name"]

    @property
    def name(self): return self._name
    @property
    def unique_id(self): return f"domo_cov_{self._id}"
    @property
    def device_class(self): return CoverDeviceClass.SHUTTER

    @property
    def is_opening(self): return "isgoingup" in self.coord.data.get(self._id, {})
    @property
    def is_closing(self): return "isgoingdown" in self.coord.data.get(self._id, {})

    async def async_open_cover(self, **kwargs): 
        await self.hub.send_command(self._id, "turnup")
        await self.coord.async_request_refresh()

    async def async_close_cover(self, **kwargs): 
        await self.hub.send_command(self._id, "turndown")
        await self.coord.async_request_refresh()

    async def async_stop_cover(self, **kwargs): 
        await self.hub.send_command(self._id, "stop")
        await self.coord.async_request_refresh()