from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.core import HomeAssistant
from datetime import timedelta
import aiohttp
import xml.etree.ElementTree as ET
from .const import DOMAIN, CONF_URL, CONF_USERNAME, CONF_PASSWORD, _LOGGER

class DomologicaDataUpdateCoordinator(DataUpdateCoordinator):
    """Gestione aggiornamento dati Domologica."""

    def __init__(self, hass: HomeAssistant, entry):
        self.hass = hass
        self.entry = entry
        self.url = entry.data[CONF_URL]
        self.username = entry.data[CONF_USERNAME]
        self.password = entry.data[CONF_PASSWORD]

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
        )

    async def _async_update_data(self):
        """Scarica dati XML remoto e ritorna come dict."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.url, auth=aiohttp.BasicAuth(self.username, self.password)
                ) as resp:
                    resp.raise_for_status()
                    xml_text = await resp.text()
                    root = ET.fromstring(xml_text)

                    data = {}
                    for elem_status in root.findall("ElementStatus"):
                        element_id = elem_status.find("ElementPath").text
                        status_dict = {}
                        for status in elem_status.findall("Status"):
                            status_id = status.attrib.get("id")
                            value_elem = status.find("value")
                            if value_elem is not None:
                                status_dict[status_id] = value_elem.text
                            else:
                                # status senza valore
                                status_dict[status_id] = None
                        data[element_id] = status_dict
                    return data
        except Exception as err:
            raise UpdateFailed(f"Errore aggiornamento dati Domologica: {err}") from err
