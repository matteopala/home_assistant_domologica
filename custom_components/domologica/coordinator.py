import asyncio
import logging
from datetime import timedelta
import aiohttp
import async_timeout
import xml.etree.ElementTree as ET

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

class DomologicaDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinatore per recuperare dati Domologica via XML remoto."""

    def __init__(self, hass, url: str, username: str, password: str, update_interval: int = 2):
        """Inizializza il coordinatore."""
        self.hass = hass
        self.url = url
        self.username = username
        self.password = password

        super().__init__(
            hass,
            _LOGGER,
            name="Domologica Coordinator",
            update_interval=timedelta(seconds=update_interval),
        )

    async def _async_update_data(self):
        """Recupera dati dal server Domologica."""
        try:
            async with async_timeout.timeout(10):
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        self.url, auth=aiohttp.BasicAuth(self.username, self.password)
                    ) as response:
                        if response.status != 200:
                            raise UpdateFailed(f"Errore HTTP {response.status}")
                        text = await response.text()
                        return self.parse_xml(text)
        except Exception as err:
            raise UpdateFailed(f"Errore durante il recupero dei dati: {err}") from err

    def parse_xml(self, xml_string: str):
        """Parsa l'XML e restituisce un dizionario con i dati."""
        data = {}
        try:
            root = ET.fromstring(xml_string)
            for element_status in root.findall("ElementStatus"):
                element_path = element_status.findtext("ElementPath")
                element_data = {}
                for status in element_status.findall("Status"):
                    status_id = status.get("id")
                    value = status.findtext("value")
                    element_data[status_id] = value
                data[element_path] = element_data
        except ET.ParseError as err:
            _LOGGER.error("Errore nel parsing XML: %s", err)
        return data
