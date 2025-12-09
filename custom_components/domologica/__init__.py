"""Domologica integration for Home Assistant via HACS"""

from homeassistant.helpers import discovery
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import requests
from requests.auth import HTTPBasicAuth

DOMAIN = "domologica"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Domologica from a config entry."""
    url = entry.data["domologica_url"]
    username = entry.data["username"]
    password = entry.data["password"]

    # Salva URL nel data dict
    hass.data[DOMAIN] = {"url": url, "username": username, "password": password}

    # Prova a leggere l'endpoint (sincrono dentro executor)
    def fetch():
        response = requests.get(url, auth=HTTPBasicAuth(username, password), timeout=10)
        response.raise_for_status()
        return response.text

    try:
        xml_data = await hass.async_add_executor_job(fetch)
    except Exception as e:
        # Fallimento connessione → log e termina setup
        hass.logger.error("Errore connessione Domologica: %s", e)
        return False

    # Carica piattaforme
    hass.async_create_task(
        discovery.async_load_platform(hass, "light", DOMAIN, {}, entry)
    )
    hass.async_create_task(
        discovery.async_load_platform(hass, "cover", DOMAIN, {}, entry)
    )
    hass.async_create_task(
        discovery.async_load_platform(hass, "sensor", DOMAIN, {}, entry)
    )

    return True
