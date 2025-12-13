import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import aiohttp
import xml.etree.ElementTree as ET
from .const import DOMAIN, CONF_URL, CONF_USERNAME, CONF_PASSWORD

class DomologicaFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Gestione config flow per Domologica."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Step iniziale per configurazione tramite interfaccia web."""
        errors = {}

        if user_input is not None:
            url = user_input[CONF_URL]
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]

            # prova a leggere l'XML remoto
            try:
                session = async_get_clientsession(self.hass)
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, auth=aiohttp.BasicAuth(username, password)) as resp:
                        resp.raise_for_status()
                        xml_text = await resp.text()
                        ET.fromstring(xml_text)  # controllo valido XML
            except aiohttp.ClientResponseError as err:
                errors["base"] = "invalid_auth" if err.status == 401 else "cannot_connect"
            except Exception:
                errors["base"] = "cannot_connect"
            else:
                # crea la configurazione
                return self.async_create_entry(
                    title="Domologica",
                    data={
                        CONF_URL: url,
                        CONF_USERNAME: username,
                        CONF_PASSWORD: password,
                    }
                )

        # form per inserimento credenziali
        data_schema = vol.Schema({
            vol.Required(CONF_URL): str,
            vol.Required(CONF_USERNAME): str,
            vol.Required(CONF_PASSWORD): str,
        })

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)
