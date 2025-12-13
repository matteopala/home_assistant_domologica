import voluptuous as vol
import logging

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import CONF_NAME, CONF_PATH

DOMAIN = "domologica"
_LOGGER = logging.getLogger(__name__)

class DomologicaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Domologica."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            xml_path = user_input.get(CONF_PATH)
            if not xml_path:
                errors["base"] = "invalid_path"
            else:
                # Aggiunge la configurazione
                return self.async_create_entry(
                    title=user_input.get(CONF_NAME, "Domologica"),
                    data=user_input
                )

        # Mostra il form all'utente
        data_schema = vol.Schema({
            vol.Required(CONF_NAME, default="Domologica"): str,
            vol.Required(CONF_PATH, default="/config/domologica_data.xml"): str
        })
        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors
        )
