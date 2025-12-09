import aiohttp
import logging
from homeassistant.helpers.entity import Entity
from datetime import timedelta
from homeassistant.helpers.event import async_track_time_interval
import asyncio

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=5)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Setup delle tapparelle Domologica."""
    url = hass.data["domologica_url"]
    manager = DomologicaManager(url)
    await manager.update_devices()

    entities = [
        DomologicaShutter(manager, name, info["xpath"])
        for name, info in manager.devices.items() if info["type"] == "shutter"
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
                import lxml.etree as etree
                tree = etree.fromstring(xml_text.encode())
                # Tapparelle
                for shutter in tree.xpath("//devices/shutters/shutters/*"):
                    name = f"{shutter.tag}"
                    xpath = f"//devices/shutters/shutters/{shutter.tag}"
                    self.devices[f"shutter_{name}"] = {"xpath": xpath, "type": "shutter"}
                    value = tree.xpath(xpath + "/text()")
                    self.cache[xpath] = value[0] if value else None
            except Exception as e:
                _LOGGER.error(f"Errore aggiornamento tapparelle Domologica: {e}")


class DomologicaShutter(Entity):
    """Tapparella Domologica con comando POST."""

    def __init__(self, manager, name, xpath, command_base_url=None, auth=None):
        self._manager = manager
        self._name = name
        self._xpath = xpath
        self._position = 0  # 0 = chiusa, 100 = aperta
        self._command_base_url = command_base_url
        self._auth = auth

    @property
    def name(self):
        return self._name

    @property
    def current_cover_position(self):
        return self._position

    @property
    def is_closed(self):
        return self._position == 0

    async def _send_command(self, action: str):
        """Invia comando alla centralina Domologica."""
        if not self._command_base_url:
            return
        url = f"{self._command_base_url}?action={action}"
        try:
            async with aiohttp.ClientSession() as session:
                auth = None
                if self._auth:
                    auth = aiohttp.BasicAuth(*self._auth)
                async with session.post(url, auth=auth) as resp:
                    if resp.status == 200:
                        _LOGGER.debug(f"{self._name}: comando '{action}' inviato con successo")
                    else:
                        _LOGGER.error(f"{self._name}: errore comando '{action}', status {resp.status}")
        except Exception as e:
            _LOGGER.error(f"{self._name}: eccezione comando '{action}': {e}")

    async def async_open_cover(self, **kwargs):
        await self._send_command("turnup")
        self._position = 100

    async def async_close_cover(self, **kwargs):
        await self._send_command("turndown")
        self._position = 0

    async def async_update(self):
        async with self._manager.lock:
            value = self._manager.cache.get(self._xpath)
            if value is not None:
                self._position = int(value)
