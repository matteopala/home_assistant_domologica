import logging
from homeassistant.components.sensor import SensorEntity
import asyncio
from datetime import timedelta
from homeassistant.helpers.event import async_track_time_interval
from lxml import etree
import aiohttp

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=5)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Setup dei sensori Domologica."""
    url = hass.data["domologica_url"]
    manager = DomologicaManager(url)
    await manager.update_devices()

    entities = [
        DomologicaGenericSensor(manager, name, info["xpath"])
        for name, info in manager.devices.items() if info["type"] == "sensor"
    ]

    async_add_entities(entities, True)
    async_track_time_interval(hass, lambda now: manager.update_devices(), SCAN_INTERVAL)


class DomologicaManager:
    """Gestisce XML e cache dei dispositivi."""

    def __init__(self, url):
        self._url = url
        self.devices = {}
        self.cache = {}
        self.lock = asyncio.Lock()

    async def fetch_xml(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self._url) as resp:
                return await resp.text()

    async def update_devices(self):
        async with self.lock:
            try:
                xml_text = await self.fetch_xml()
                tree = etree.fromstring(xml_text.encode())
                # Sensori generici
                for sensor in tree.xpath("//devices/sensors/*"):
                    name = f"{sensor.tag}"
                    xpath = f"//devices/sensors/{sensor.tag}"
                    self.devices[f"sensor_{name}"] = {"xpath": xpath, "type": "sensor"}
                    value = tree.xpath(xpath + "/text()")
                    self.cache[xpath] = value[0] if value else None
            except Exception as e:
                _LOGGER.error(f"Errore aggiornamento sensori Domologica: {e}")


class DomologicaGenericSensor(SensorEntity):
    """Sensore generico Domologica."""

    def __init__(self, manager, name, xpath):
        self._manager = manager
        self._name = name
        self._xpath = xpath
        self._state = None

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    async def async_update(self):
        async with self._manager.lock:
            self._state = self._manager.cache.get(self._xpath)
