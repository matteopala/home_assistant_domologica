import aiohttp
import logging
from homeassistant.components.light import LightEntity
from datetime import timedelta
from homeassistant.helpers.event import async_track_time_interval
import asyncio
from lxml import etree

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=5)
DOMAIN = "domologica"


async def async_setup_entry(hass, entry, async_add_entities):
    """Setup luci Domologica da config entry."""
    url = entry.data["domologica_url"]
    username = entry.data["username"]
    password = entry.data["password"]

    manager = DomologicaManager(url, username, password)
    await manager.update_devices()

    entities = [
        DomologicaLight(manager, name, info["xpath"])
        for name, info in manager.devices.items() if info["type"] == "light"
    ]

    async_add_entities(entities, True)

    async def update_loop(now):
        await manager.update_devices()
        for entity in entities:
            await entity.async_update_ha_state()

    async_track_time_interval(hass, update_loop, SCAN_INTERVAL)


class DomologicaManager:
    """Gestisce XML e cache luci."""

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
                for light in tree.xpath("//devices/lights/lights/*"):
                    name = f"{light.tag}"
                    xpath = f"//devices/lights/lights/{light.tag}"
                    self.devices[f"light_{name}"] = {"xpath": xpath, "type": "light"}
                    value = tree.xpath(xpath + "/text()")
                    self.cache[xpath] = value[0] if value else None
            except Exception as e:
                _LOGGER.error(f"Errore aggiornamento luci Domologica: {e}")


class DomologicaLight(LightEntity):
    """Luce Domologica."""

    def __init__(self, manager, name, xpath):
        self._manager = manager
        self._name = name
        self._xpath = xpath
        self._is_on = False

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        return self._is_on

    async def async_turn_on(self, **kwargs):
        self._is_on = True

    async def async_turn_off(self, **kwargs):
        self._is_on = False

    async def async_update(self):
        async with self._manager.lock:
            value = self._manager.cache.get(self._xpath)
            self._is_on = value == "1"
