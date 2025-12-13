import logging
import asyncio
import aiohttp
import xml.etree.ElementTree as ET
from datetime import timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

class DomologicaDataUpdateCoordinator(DataUpdateCoordinator):
    """Gestisce il polling dei dati Domologica."""

    def __init__(self, hass, url, username, password, update_interval=2, logger=_LOGGER):
        """Inizializza il coordinator."""
        self.hass = hass
        self.url = url
        self.username = username
        self.password = password
        self.logger = logger

        # Trasforma l'update_interval in timedelta
        interval = timedelta(seconds=update_interval)

        super().__init__(
            hass,
            logger,
            name="Domologica Data Coordinator",
            update_interval=interval,
        )

    async def _async_update_data(self):
        """Fetch dei dati da Domologica in modo asincrono."""
        try:
            async with aiohttp.ClientSession() as session:
                auth = aiohttp.BasicAuth(self.username, self.password)
                async with session.get(self.url, auth=auth) as response:
                    if response.status != 200:
                        raise UpdateFailed(f"Errore HTTP: {response.status}")
                    text = await response.text()

            # Parsing XML
            try:
                root = ET.fromstring(text)
            except ET.ParseError as e:
                raise UpdateFailed(f"Errore parsing XML: {e}")

            # Ritorna un dict dei dati da usare nei sensori
            data = {}
            for element in root.findall("ElementStatus"):
                element_path = element.find("ElementPath").text
                statuses = {}
                for status in element.findall("Status"):
                    status_id = status.attrib.get("id")
                    value_elem = status.find("value")
                    value = value_elem.text if value_elem is not None else None
                    statuses[status_id] = value
                data[element_path] = statuses

            return data

        except Exception as e:
            raise UpdateFailed(f"Errore fetching dati Domologica: {e}")
