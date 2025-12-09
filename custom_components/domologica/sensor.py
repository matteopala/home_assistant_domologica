import logging
from homeassistant.components.sensor import SensorEntity
from datetime import timedelta
from homeassistant.helpers.event import async_track_time_interval
from lxml import etree
import aiohttp
import asyncio

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=5)
DOMAIN = "domologica"

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Domologica sensors from a config entry."""
    url = entry.data["domologica_url"]
    username = entry.data["username"]
    password = entry.data["password"]

    manager = DomologicaManager(url, username, password)
    await manager.update_devices()

    entities = [
        DomologicaGenericSensor(manager, name, info["xpath"])
        for name, info in manager.devices.items() if info["type"] == "sensor"
    ]

    async_add_entities(entities, True)

    # Aggiornamento periodico
    async def update_loop(now):
        await manager.update_devices()
        for entity in entities:
            await entity.async_update_ha_state()

    async_track_time_interval(hass, update_loop, SCAN_INTERVAL)


class DomologicaManager:
    """Gestisce XML e cache dei dispositivi."""

    def __init__(self, url, username, password):
        self._url = url
        self._auth = aiohttp.BasicAuth(username, password)
        self.devices = {}
        self.cache = {}
        self.lock = asyncio.Lock()

    async def fetch_xml(self):
        async with aiohttp.ClientSession(auth=self._auth) as session:
            async with session.get(self._url) as resp:
                resp.raise_for_status()
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
