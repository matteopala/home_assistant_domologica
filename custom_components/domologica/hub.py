import aiohttp
import xml.etree.ElementTree as ET
import logging
import asyncio

_LOGGER = logging.getLogger(__name__)

class DomologicaHub:
    def __init__(self, host, username, password):
        self.host = host
        # Crea l'autenticazione Basic una volta sola
        self.auth = aiohttp.BasicAuth(username, password)
        self.devices = {}

    async def async_discover(self):
        """Scansiona gli elementi usando le credenziali fornite."""
        _LOGGER.info("Connessione a %s con utente %s...", self.host, self.auth.login)
        async with aiohttp.ClientSession() as session:
            for i in range(1, 301):
                url = f"http://{self.host}/api/elements/{i}.xml"
                try:
                    async with session.get(url, auth=self.auth, timeout=1) as resp:
                        if resp.status == 200:
                            text = await resp.text()
                            root = ET.fromstring(text)
                            self.devices[str(i)] = {
                                "id": str(i),
                                "name": root.findtext("name", f"Device {i}").strip(),
                                "classId": root.findtext("classId"),
                            }
                except Exception:
                    continue
        return self.devices

    async def get_all_statuses(self):
        """Scarica lo stato globale usando l'autenticazione."""
        url = f"http://{self.host}/api/element_xml_statuses.xml"
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, auth=self.auth, timeout=10) as resp:
                    if resp.status != 200:
                        _LOGGER.error("Errore autenticazione o connessione: %s", resp.status)
                        return {}
                    
                    text = await resp.text()
                    root = ET.fromstring(text)
                    all_data = {}
                    
                    for element in root.findall("ElementStatus"):
                        eid = element.findtext("ElementPath")
                        if not eid: continue
                        
                        device_states = {}
                        for status in element.findall("Status"):
                            s_id = status.get("id")
                            val_tag = status.find("value")
                            val = val_tag.text if val_tag is not None else True
                            device_states[s_id] = val
                        all_data[eid] = device_states
                    return all_data
            except Exception as e:
                _LOGGER.error("Eccezione durante il polling: %s", e)
                return {}

    async def send_command(self, device_id, action, value=None):
        """Invia comandi autenticati."""
        url = f"http://{self.host}/elements/{device_id}.xml?action={action}"
        if value is not None: url += f"&value={value}"
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, auth=self.auth, timeout=5) as resp:
                    return resp.status == 200
            except Exception as e:
                _LOGGER.error("Errore comando %s su ID %s: %s", action, device_id, e)
                return False