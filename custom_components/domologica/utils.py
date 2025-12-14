from __future__ import annotations

import asyncio
import xml.etree.ElementTree as ET

from aiohttp import ClientError, ClientTimeout
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

        text = await resp.text()
        return ET.fromstring(text)


async def async_set_dimmer(
    hass: HomeAssistant,
    base_url: str,
    element_id: str,
    brightness: int,
    username: str | None,
    password: str | None,
) -> ET.Element:
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

        text = await resp.text()
        return ET.fromstring(text)


async def async_command(
    hass: HomeAssistant,
    base_url: str,
    element_id: str,
    action: str,
    username: str | None,
    password: str | None,
) -> None:
    url = f"{base_url}/elements/{element_id}.xml?action={action}"

    auth = None
    if username and password:
        from aiohttp import BasicAuth

        auth = BasicAuth(username, password)

    session = hass.helpers.aiohttp_client.async_get_clientsession(hass)
    async with session.get(url, auth=auth, timeout=_TIMEOUT) as resp:
        resp.raise_for_status()


async def async_test_connection(
    hass: HomeAssistant,
    base_url: str,
    username: str | None,
    password: str | None,
) -> bool:
    try:
        await async_fetch_element_statuses(hass, base_url, username, password)
        return True
    except Exception:
        return False


def element_by_id(root: ET.Element, element_id: str) -> ET.Element | None:
    return root.find(f".//ElementStatus[ElementPath='{element_id}']")


def list_elements(root: ET.Element) -> list[tuple[str, str | None]]:
    """
    Ritorna lista di (element_id, element_name)
    Il nome viene dedotto da status noti o parametri descrittivi.
    """
    out: list[tuple[str, str | None]] = []
    for e in root.findall("ElementStatus"):
        eid = e.findtext("ElementPath")
        if not eid:
            continue

        # Tentativo di naming: status 'parameter' o simili
        name = None
        param = e.find(".//Status[@id='parameter']/value")
        if param is not None and param.text:
            name = param.text.split(":")[0]

        out.append((str(eid), name))
    return out


def list_element_ids(root: ET.Element) -> list[str]:
    out: list[str] = []
    for e in root.findall("ElementStatus"):
        eid = e.findtext("ElementPath")
        if eid:
            out.append(str(eid))
    return out


def list_status_ids_with_value(elem: ET.Element) -> list[str]:
    ids: list[str] = []
    for s in elem.findall("Status"):
        sid = s.attrib.get("id")
        if sid and s.find("value") is not None:
            ids.append(sid)
    return ids


def has_status(elem: ET.Element, status_id: str) -> bool:
    return elem.find(f".//Status[@id='{status_id}']") is not None


def read_value(elem: ET.Element, status_id: str) -> str | None:
    v = elem.find(f".//Status[@id='{status_id}']/value")
    return v.text if v is not None else None


def normalize_entity_name(element_id: str, element_name: str | None = None, status_id: str | None = None) -> str:
    """
    Costruisce nomi leggibili per device ed entità.
    Priorità:
    1) Nome elemento (se disponibile)
    2) ElementPath
    3) Status id (per sensori)
    """
    base = element_name or f"Element {element_id}"
    if status_id:
        return f"{base} {status_id}".replace("  ", " ")
    return base