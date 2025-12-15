from __future__ import annotations

import logging
import xml.etree.ElementTree as ET

from aiohttp import BasicAuth, ClientTimeout, ClientResponseError
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)
_TIMEOUT = ClientTimeout(total=30)


def _auth(username: str | None, password: str | None):
    if username and password:
        return BasicAuth(username, password)
    return None


async def async_fetch_element_statuses(
    hass: HomeAssistant,
    base_url: str,
    username: str | None,
    password: str | None,
) -> ET.Element:
    url = f"{base_url.rstrip('/')}/api/element_xml_statuses.xml"
    session = async_get_clientsession(hass)
    auth = _auth(username, password)

    try:
        async with session.get(url, auth=auth, timeout=_TIMEOUT) as resp:
            # ✅ niente log a livello warning in polling
            _LOGGER.debug("Domologica GET %s -> HTTP %s", url, resp.status)
            resp.raise_for_status()
            text = await resp.text()
            return ET.fromstring(text)

    except ClientResponseError as err:
        # ✅ log solo su errori HTTP
        _LOGGER.error("Domologica HTTP error %s on %s", err.status, url)
        raise
    except Exception as err:
        _LOGGER.error("Domologica connection error on %s: %s", url, err)
        raise


def parse_statuses(root: ET.Element) -> dict[str, dict[str, object]]:
    """Converte l'XML in dict indicizzato: { '48': {'getdimmer': '51', 'isswitchedoff': True}, ... }"""
    elements: dict[str, dict[str, object]] = {}

    for el in root.findall("ElementStatus"):
        eid = el.findtext("ElementPath")
        if not eid:
            continue

        st: dict[str, object] = {}
        for s in el.findall("Status"):
            sid = s.attrib.get("id")
            if not sid:
                continue
            v = s.find("value")
            if v is None:
                st[sid] = True
            else:
                st[sid] = v.text or ""
        elements[str(eid)] = st

    return elements


async def async_command(
    hass: HomeAssistant,
    base_url: str,
    element_id: str,
    action: str,
    username: str | None,
    password: str | None,
) -> None:
    url = f"{base_url.rstrip('/')}/elements/{element_id}.xml?action={action}"
    session = async_get_clientsession(hass)
    auth = _auth(username, password)

    async with session.get(url, auth=auth, timeout=_TIMEOUT) as resp:
        _LOGGER.debug("Domologica CMD %s -> HTTP %s", url, resp.status)
        resp.raise_for_status()


async def async_set_dimmer(
    hass: HomeAssistant,
    base_url: str,
    element_id: str,
    value: int,
    username: str | None,
    password: str | None,
) -> None:
    url = f"{base_url.rstrip('/')}/elements/{element_id}.xml?action=setdimmer"
    session = async_get_clientsession(hass)
    auth = _auth(username, password)

    data = {
        "arguments[0][value]": str(int(value)),
        "arguments[0][type]": "int",
    }

    async with session.post(url, data=data, auth=auth, timeout=_TIMEOUT) as resp:
        _LOGGER.debug("Domologica DIMMER %s -> HTTP %s", url, resp.status)
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


def normalize_entity_name(
    element_id: str,
    element_name: str | None = None,
    status_id: str | None = None,
) -> str:
    base = element_name or f"Element {element_id}"
    if status_id:
        return f"{base} {status_id}".replace("  ", " ")
    return base
