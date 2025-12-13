import async_timeout
import aiohttp
import xml.etree.ElementTree as ET
from datetime import timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.core import HomeAssistant

from .const import DOMAIN, ON_KEYWORDS, OFF_KEYWORDS

class DomologicaCoordinator(DataUpdateCoordinator):
def __init__(self, hass: HomeAssistant, session, config):
self.url = config["url"]
self.auth = aiohttp.BasicAuth(config["username"], config["password"])

super().__init__(
hass,
logger=None,
name=DOMAIN,
update_interval=timedelta(seconds=config["scan_interval"]),
)
self.session = session

async def _async_update_data(self):
try:
async with async_timeout.timeout(15):
async with self.session.get(self.url, auth=self.auth) as resp:
if resp.status != 200:
raise UpdateFailed(f"HTTP {resp.status}")
text = await resp.text()
except Exception as err:
raise UpdateFailed(err)

return self._parse_xml(text)

def _parse_xml(self, xml_text):
data = {}
root = ET.fromstring(xml_text)

for el in root.findall("ElementStatus"):
element_id = el.findtext("ElementPath")
if not element_id:
continue

statuses = {s.attrib.get("id", "").lower(): s for s in el.findall("Status")}

is_on = None
for k in statuses.keys():
if k in ON_KEYWORDS:
is_on = True
if k in OFF_KEYWORDS:
is_on = False

data[element_id] = {
"on": is_on,
"statuses": statuses,
}

return data