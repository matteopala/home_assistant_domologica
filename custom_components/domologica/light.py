import aiohttp
from lxml import etree
import logging
from homeassistant.helpers.entity import Entity
from datetime import timedelta
from homeassistant.helpers.event import async_track_time_interval
import asyncio

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=5)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Setup delle luci Domologica."""
    url = hass.data["domologica_url"]
    manager = DomologicaManager(url)
    await manager.update_devices()

    entities = [
        DomologicaLight(manager, name, info["xpath"])
        for name, info in manager.devices.items() if info["type"] == "light"
    ]

    async_add_entities(entities, True)
    async_track_time_interval(hass, lambda now: manager.update_devices(), SCAN_INTERVAL)


class DomologicaManager:
    """Gestisce XML e cache dei dispositivi."""

    def __init__(self, url):
        self._url = url
        self.devices = {}  # {nome: {"xpath": xpath, "type": categoria}}
        self.cache = {}    # {xpath: stato}
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
                # Luci
                for light in tree.xpath("//devices/lights/lights/*"):
                    name = f"{light.tag}"
                    xpath = f"//devices/lights/lights/{light.tag}"
                    self.devices[f"light_{name}"] = {"xpath": xpath, "type": "light"}
                    value = tree.xpath(xpath + "/text()")
                    self.cache[xpath] = value[0] if value else None
            except Exception as e:
                _LOGGER.error(f"Errore aggiornamento luci Domologica: {e}")


class DomologicaLight(Entity):
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
        """Accendi la luce (da implementare comando reale se disponibile)."""
        self._is_on = True

    async def async_turn_off(self, **kwargs):
        """Spegni la luce (da implementare comando reale se disponibile)."""
        self._is_on = False

    async def async_update(self):
        async with self._manager.lock:
            value = self._manager.cache.get(self._xpath)
            self._is_on = value == "1"
