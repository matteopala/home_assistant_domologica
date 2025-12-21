from homeassistant.components.light import LightEntity, ColorMode, ATTR_BRIGHTNESS
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    d = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([DomoLight(d["coord"], d["hub"], info) for eid, info in d["hub"].devices.items() if "Light" in info["classId"]])

class DomoLight(LightEntity):
    def __init__(self, coord, hub, info):
        self.coord, self.hub, self._id, self._name = coord, hub, info["id"], info["name"]
        self._is_dim = "Dimmerable" in info["classId"]

    @property
    def name(self): return self._name
    @property
    def unique_id(self): return f"domo_light_{self._id}"

    @property
    def is_on(self):
        st = self.coord.data.get(self._id, {})
        if "isswitchedoff" in st: return False
        if "isswitchedon" in st: return True
        return False

    @property
    def brightness(self):
        if not self._is_dim: return None
        v = self.coord.data.get(self._id, {}).get("getdimmer")
        return int((int(v)/100)*255) if v and str(v).isdigit() else 0

    @property
    def supported_color_modes(self): return {ColorMode.BRIGHTNESS} if self._is_dim else {ColorMode.ONOFF}
    @property
    def color_mode(self): return ColorMode.BRIGHTNESS if self._is_dim else ColorMode.ONOFF

    async def async_turn_on(self, **kwargs):
        if ATTR_BRIGHTNESS in kwargs and self._is_dim:
            val = int((kwargs[ATTR_BRIGHTNESS]/255)*100)
            await self.hub.send_command(self._id, "setdimmer", val)
        else: await self.hub.send_command(self._id, "switchon")
        await self.coord.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self.hub.send_command(self._id, "switchoff")
        await self.coord.async_request_refresh()