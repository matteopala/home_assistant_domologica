from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import HVACMode, ClimateEntityFeature
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    d = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([DomoClimate(d["coord"], d["hub"], info) for eid, info in d["hub"].devices.items() if "Thermostat" in info["classId"] or "Samsung" in info["classId"]])

class DomoClimate(ClimateEntity):
    def __init__(self, coord, hub, info):
        self.coord, self.hub, self._id, self._name = coord, hub, info["id"], info["name"]
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL]
        self._attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE

    @property
    def name(self): return self._name
    @property
    def unique_id(self): return f"domo_clim_{self._id}"

    @property
    def current_temperature(self):
        st = self.coord.data.get(self._id, {})
        # Prova temperatureN (Termostato) o Room Temp (Samsung)
        val = st.get("temperatureN") or st.get("Get AC unit Temperature Room")
        return float(val) if val else None

    @property
    def target_temperature(self):
        st = self.coord.data.get(self._id, {})
        val = st.get("tMin") or st.get("Get AC unit Temperature Setted")
        return float(val) if val else None

    @property
    def hvac_mode(self):
        st = self.coord.data.get(self._id, {})
        if "IsSwitchedOff" in st or "statusoff" in st: return HVACMode.OFF
        if "Winter" in str(st.get("season")) or "Heat" in str(st): return HVACMode.HEAT
        return HVACMode.COOL

    async def async_set_hvac_mode(self, hvac_mode):
        act = "switchoff" if hvac_mode == HVACMode.OFF else "switchon"
        await self.hub.send_command(self._id, act)
        await self.coord.async_request_refresh()

    async def async_set_temperature(self, **kwargs):
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp:
            # Sceglie il comando in base al tipo di dispositivo
            st = self.coord.data.get(self._id, {})
            cmd = "setTMode" if "temperatureN" in st else "settemperaturedesired"
            await self.hub.send_command(self._id, cmd, temp)
            await self.coord.async_request_refresh()