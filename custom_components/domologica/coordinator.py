import logging
import aiohttp
import xml.etree.ElementTree as ET
from datetime import timedelta

from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)


class DomologicaDataUpdateCoordinator(DataUpdateCoordinator):
    """Gestisce il polling dei dati Domologica."""

    def __init__(
        self,
        hass,
        url: str,
        username: str,
        password: str,
        update_interval: int = 2,
    ):
        """Inizializza il coordinator."""
        self.url = url
        self.username = username
        self.password = password

        super().__init__(
            hass,
            _LOGGER,
            name="Domologica Data Coordinator",
            update_interval=timedelta(seconds=update_interval),
        )

    async def _async_update_data(self):
        """Fetch dei dati da Domologica in modo asincrono."""
        session = async_get_clientsession(self.hass)
        auth = aiohttp.BasicAuth(self.username, self.password)

        try:
            async with session.get(
                self.url,
                auth=auth,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status != 200:
                    raise UpdateFailed(f"Errore HTTP {response.status}")

                text = await response.text()

        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Errore connessione Domologica: {err}") from err

        # Parsing XML
        try:
            root = ET.fromstring(text)
        except ET.ParseError as err:
            raise UpdateFailed(f"Errore parsing XML: {err}") from err

        data: dict[str, dict[str, str | None]] = {}

        for element in root.findall("ElementStatus"):
            element_path_el = element.find("ElementPath")
            if element_path_el is None:
                continue

            element_path = element_path_el.text
            statuses: dict[str, str | None] = {}

            for status in element.findall("Status"):
                status_id = status.attrib.get("id")
                if not status_id:
                    continue

                value_el = status.find("value")
                statuses[status_id] = value_el.text if value_el is not None else None

            data[element_path] = statuses

        return data
