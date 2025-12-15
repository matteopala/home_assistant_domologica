from __future__ import annotations

import logging
import xml.etree.ElementTree as ET

from aiohttp import ClientTimeout, ClientResponseError
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

# timeout più largo per dispositivi lenti
_TIMEOUT = ClientTimeout(total=30)


def _get_auth(username: str | None, password: str | None):
    if username and password:
        from aiohttp import BasicAuth

        return BasicAuth(username, password)
    return None


async def async_fetch_element_statuses(
    hass: HomeAssistant,
    base_url: str,
    username: str | None,
    password: str | None,
) -> ET.Element:
    """
    Scarica e parse l'XML principale:
    /api/element_xml_statuses.xml
    """
    url = f"{base_url}/api/element_xml_statuses.xml"
    auth = _get_auth(username, password)

    session = hass.helpers.aiohttp_client.async_get_clientsession(hass)

    _LOGGER.debug("Domologica GET %s", url)

    try:
        async with session.get(url, auth=auth, timeout=_TIMEOUT) as resp:
            _LOGGER.debug(
                "Domologica response status=%s for %s", resp.status, url
            )
            resp.raise_for_status()
            text = await resp.text()
            return ET.fromstring(text)

    except ClientResponseError as err:
        _LOGGER.error(
            "Domologica HTTP error %s on %s", err.status, url
        )
        raise

    except Exception as err:
        _LOGGER.error(
            "Domologica connection error on %s: %s", url, err
        )
        raise


async def async_command(
    hass: HomeAssistant,
    base_url: str,
    element_id: str,
    action: str,
    username: str | None,
    password: str | None,
) -> None:
    """
    Comando generico GET:
    /elements/{id}.xml?action=...
    """
    url = f"{base_url}/elements/{element_id}.xml?action={action}"
    auth = _get_auth(username, password)

    session = hass.helpers.aiohttp_client.async_get_clientsession(hass)

    _LOGGER.debug("Domologica COMMAND %s", url)

    async with session.get(url, auth=auth, timeout=_TIMEOUT) as resp:
        _LOGGER.debug(
            "Domologica command response status=%s for %s",
            resp.status,
            url,
        )
        resp.raise_for_status()


async def async_set_dimmer(
    hass: HomeAssistant,
    base_url: str,
    element_id: str,
    value: int,
    username: str | None,
    password: str | None,
) -> None:
    """
    Imposta il dimmer via POST:
    action=setdimmer
    arguments[0][value]=X
    arguments[0][type]=int
    """
    url = f"{base_url}/elements/{element_id}.xml?action=setdimmer"
    auth = _get_auth(username, password)

    data = {
        "arguments[0][value]": str(int(value)),
        "arguments[0][type]": "int",
    }

    session = hass.helpers.aiohttp_client.async_get_clientsession(hass)

    _LOGGER.debug(
        "Domologica DIMMER POST %s value=%s", url, value
    )

    async with session.post(
        url, data=data, auth=auth, timeout=_TIMEOUT
    ) as resp:
        _LOGGER.debug(
            "Domologica dimmer response status=%s for %s",
            resp.status,
            url,
        )
        resp.raise_for_status()


async def async_test_connection(
    hass: HomeAssistant,
    base_url: str,
    username: str | None,
    password: str | None,
) -> bool:
    """
    Usato dal config_flow per testare la connessione
    """
    try:
        await async_fetch_element_statuses(
            hass, base_url, username, password
        )
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
    if status_id:
        return f"Element {element_id} {status_id}"
    if element_name:
        return element_name
    return f"Element {element_id}"
