import asyncio
import aiohttp
import xml.etree.ElementTree as ET
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

class DomologicaDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator to fetch data from Domologica XML."""

    def __init__(self, hass, url, username, password, update_interval=2):
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
        """Fetch XML data from Domologica remote."""
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url, auth=aiohttp.BasicAuth(self.username, self.password)) as response:
                if response.status != 200:
                    raise Exception(f"HTTP error {response.status}")
                xml_text = await response.text()

        # Parse XML
        root = ET.fromstring(xml_text)
        data = {}
        for elem_status in root.findall("ElementStatus"):
            path = elem_status.findtext("ElementPath")
            values = {}
            for status in elem_status.findall("Status"):
                status_id = status.get("id")
                value = status.findtext("value")
                if value is not None:
                    values[status_id] = value
            data[path] = values
        return data
