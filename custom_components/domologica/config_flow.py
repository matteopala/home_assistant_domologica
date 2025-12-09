import voluptuous as vol
import requests
from requests.auth import HTTPBasicAuth
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

DOMAIN = "domologica"

DATA_SCHEMA = vol.Schema({
    vol.Required("domologica_url"): str,
    vol.Required("username"): str,
    vol.Required("password"): str
})

class DomologicaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Domologica."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            # Prova a connettersi all'URL con le credenziali inserite
            try:
                response = requests.get(
                    user_input["domologica_url"],
                    auth=HTTPBasicAuth(user_input["username"], user_input["password"]),
                    timeout=10
                )
                response.raise_for_status()
            except requests.exceptions.RequestException:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(title="Domologica", data=user_input)

        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA, errors=errors)
