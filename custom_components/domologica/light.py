import logging
import asyncio
import xml.etree.ElementTree as ET

from homeassistant.components.light import LightEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

# Lista dei dispositivi da creare (puoi aggiornare con tutti gli ElementPath che vuoi)
ELEMENTS = {
    "57": "Light Studio",
    "40": "Light Sala",  # esempio aggiuntivo
    # aggiungi altri elementi qui
}

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Domologica lights."""
    session = async_get_clientsession(hass)
    devices = [DomologicaLight(hass, element_id, name) for element_id, name in ELEMENTS.items()]
    async_add_entities(devices, update_before_add=True)


class DomologicaLight(LightEntity):
    """Representation of a Domologica light."""

    def __init__(self, hass, element_id, name):
        self.hass = hass
        self._element_id = element_id
        self._name = name
        self._is_on = False

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        return self._is_on

    async def async_update(self):
        """Fetch status from the XML and update the state."""
        url = "http://192.168.5.2/api/element_xml_statuses.xml"
        auth = aiohttp.BasicAuth("residenzacanal06@gmail.com", "#&I%Afj6")
        session = async_get_clientsession(self.hass)
        try:
            async with session.get(url, auth=auth) as resp:
                text = await resp.text()
                root = ET.fromstring(text)
                for element in root.findall("ElementStatus"):
                    path = element.findtext("ElementPath")
                    if path == self._element_id:
                        status = element.find("Status")
                        if status is not None and status.attrib.get("id") == "isswitchedon":
                            self._is_on = True
                        else:
                            self._is_on = False
        except Exception as e:
            _LOGGER.error("Error fetching Domologica XML: %s", e)
