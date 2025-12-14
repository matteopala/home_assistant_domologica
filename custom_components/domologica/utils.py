from __future__ import annotations

import xml.etree.ElementTree as ET
from aiohttp import ClientTimeout
from homeassistant.core import HomeAssistant

_TIMEOUT = ClientTimeout(total=10)


async def async_fetch_element_statuses(
    hass: HomeAssistant,
    base_url: str,
    username: str | None,
    password: str | None,
) -> ET.Element:
    url = f"{base_url}/api/element_xml_statuses.xml"

    auth = None
    if username and password:
        from aiohttp import BasicAuth
        auth = BasicAuth(username, password)

    session = hass.helpers.aiohttp_client.async_get_clientsession(hass)
    async with session.get(url, auth=auth, timeout=_TIMEOUT) as resp:
        resp.raise_for_status()
        return ET.fromstring(await resp.text())


async def async_command(
    hass: HomeAssistant,
    base_url: str,
    element_id: str,
    action: str,
    username: str | None,
    password: str | None,
):
    url = f"{base_url}/elements/{element_id}.xml?action={action}"

    auth = None
    if username and password:
        from aiohttp import BasicAuth
        auth = BasicAuth(username, password)

    session = hass.helpers.aiohttp_client.async_get_clientsession(hass)
    async with session.get(url, auth=auth, timeout=_TIMEOUT) as resp:
        resp.raise_for_status()


async def async_set_dimmer(
    hass: HomeAssistant,
    base_url: str,
    element_id: str,
    brightness: int,
    username: str | None,
    password: str | None,
):
    url = (
        f"{base_url}/elements/{element_id}.xml"
        f"?action=setdimmer&arguments[0][value]={brightness}&arguments[0][type]=int"
    )

    auth = None
    if username and password:
        from aiohttp import BasicAuth
        auth = BasicAuth(username, password)

    session = hass.helpers.aiohttp_client.async_get_clientsession(hass)
    async with session.post(url, auth=auth, timeout=_TIMEOUT) as resp:
        resp.raise_for_status()


async def async_test_connection(hass, base_url, username, password) -> bool:
    try:
        await async_fetch_element_statuses(hass, base_url, username, password)
        return True
    except Exception:
        return False


# ---------- XML helpers ----------

def element_by_id(root: ET.Element, element_id: str):
    return root.find(f".//ElementStatus[ElementPath='{element_id}']")


def has_status(elem: ET.Element, status_id: str) -> bool:
    return elem.find(f".//Status[@id='{status_id}']") is not None


def read_value(elem: ET.Element, status_id: str):
    v = elem.find(f".//Status[@id='{status_id}']/value")
    return v.text if v is not None else None


def list_status_ids_with_value(elem: ET.Element):
    ids = []
    for s in elem.findall("Status"):
        if s.attrib.get("id") and s.find("value") is not None:
            ids.append(s.attrib["id"])
    return ids


def normalize_entity_name(element_id: str, element_name=None, status_id=None) -> str:
    base = element_name or f"Element {element_id}"
    if status_id:
        return f"{base} {status_id}".replace("  ", " ")
    return base
