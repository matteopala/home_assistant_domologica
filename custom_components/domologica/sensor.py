import logging
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfElectricPotential, UnitOfElectricCurrent, UnitOfPower, UnitOfTemperature
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    d = hass.data[DOMAIN][entry.entry_id]
    hub, coord = d["hub"], d["coord"]
    entities = []

    for eid, info in hub.devices.items():
        if "Inverter" in info["name"] or eid == "5":
            entities.append(DomoInverterSensor(coord, eid, "Watt", "Output Watt Phase R", UnitOfPower.WATT, SensorDeviceClass.POWER))
            entities.append(DomoInverterSensor(coord, eid, "Voltage", "Input Volt Phase R", UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE))
        if eid == "56": # Pompa di calore
            entities.append(DomoInverterSensor(coord, eid, "Water In", "Get AC unit Water In Temperature", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE))
            entities.append(DomoInverterSensor(coord, eid, "Water Out", "Get AC unit Water Out Temperature", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE))
            
    async_add_entities(entities)

class DomoInverterSensor(SensorEntity):
    def __init__(self, coord, eid, label, key, unit, device_class):
        self.coord, self._eid, self._label, self._key = coord, eid, label, key
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def name(self): return f"Domologica {self._eid} {self._label}"
    @property
    def unique_id(self): return f"domo_sens_{self._eid}_{self._label.replace(' ','_')}"

    @property
    def native_value(self):
        st = self.coord.data.get(self._eid, {})
        param_str = st.get("parameter", "")
        if isinstance(param_str, str) and self._key in param_str:
            # Esempio: "Energy Total=2200;..." -> cerca la chiave e splitta
            try:
                parts = param_str.split(';')
                for p in parts:
                    if self._key in p:
                        return float(p.split('=')[1].replace('Â°C', '').strip())
            except: return None
        # Se non è in parameter, prova come tag diretto
        val = st.get(self._key)
        return float(val) if val and str(val).replace('.','',1).isdigit() else None