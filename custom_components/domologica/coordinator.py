import logging
from datetime import timedelta
import xml.etree.ElementTree as ET

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(seconds=20)  # aggiornamento ogni 20 secondi

class DomologicaCoordinator(DataUpdateCoordinator):
    """Coordinator for Domologica integration."""

    def __init__(self, hass: HomeAssistant, xml_file_path: str):
        """Initialize the coordinator."""
        self.hass = hass
        self.xml_file_path = xml_file_path
        super().__init__(
            hass,
            _LOGGER,
            name="Domologica",
            update_interval=UPDATE_INTERVAL
        )

    async def _async_update_data(self):
        """Fetch data from XML file."""
        try:
            return await self.hass.async_add_executor_job(self._parse_xml)
        except Exception as err:
            raise UpdateFailed(f"Error fetching Domologica data: {err}") from err

    def _parse_xml(self):
        """Parse the XML file and return a dict with element statuses."""
        data = {}
        try:
            tree = ET.parse(self.xml_file_path)
            root = tree.getroot()
            for element in root.findall("ElementStatus"):
                path = element.findtext("ElementPath")
                statuses = {}
                for status in element.findall("Status"):
                    status_id = status.attrib.get("id")
                    value_elem = status.find("value")
                    if value_elem is not None:
                        try:
                            value = float(value_elem.text)
                        except (TypeError, ValueError):
                            value = value_elem.text
                    else:
                        value = status_id  # se non ha <value>, prendiamo l'id
                    statuses[status_id] = value
                data[path] = statuses
        except Exception as e:
            _LOGGER.error("Error parsing XML: %s", e)
        return data
