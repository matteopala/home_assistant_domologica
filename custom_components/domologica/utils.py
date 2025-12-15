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
            _LOGGER.warning("Domologica GET %s -> HTTP %s", url, resp.status)
            resp.raise_for_status()
            text = await resp.text()
            return ET.fromstring(text)

    except ClientResponseError as err:
        # Questo log ti dice *esattamente* se è 401/403/404 ecc.
        _LOGGER.error("Domologica HTTP error %s on %s", err.status, url)
        raise

    except Exception as err:
        _LOGGER.error("Domologica connection error on %s: %s", url, err)
        raise


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
        _LOGGER.warning("Domologica CMD %s -> HTTP %s", url, resp.status)
        resp.raise_for_status()


async def async_set_dimmer(
    hass: HomeAssistant,
    base_url: str,
    element_id: str,
    value: int,
    username: str | None,
    password: str | None,
) -> None:
    # POST autenticata: action=setdimmer + form fields arguments[0][...]
    url = f"{base_url.rstrip('/')}/elements/{element_id}.xml?action=setdimmer"
    session = async_get_clientsession(hass)
    auth = _auth(username, password)

    data = {
        "arguments[0][value]": str(int(value)),
        "arguments[0][type]": "int",
    }

    async with session.post(url, data=data, auth=auth, timeout=_TIMEOUT) as resp:
        _LOGGER.warning("Domologica DIMMER %s -> HTTP %s", url, resp.status)
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


# -------------------------
# XML helpers
# -------------------------

def element_by_id(root: ET.Element, element_id: str) -> ET.Element | None:
    return root.find(f".//ElementStatus[ElementPath='{element_id}']")


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


def normalize_entity_name(
    element_id: str,
    element_name: str | None = None,
    status_id: str | None = None,
) -> str:
    base = element_name or f"Element {element_id}"
    if status_id:
        return f"{base} {status_id}".replace("  ", " ")
    return base
