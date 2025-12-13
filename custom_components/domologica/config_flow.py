import voluptuous as vol # pyright: ignore[reportMissingImports]
from homeassistant import config_entries # pyright: ignore[reportMissingImports]
from .const import DOMAIN

class DomologicaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Domologica."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title="Domologica", data=user_input)

        data_schema = vol.Schema(
            {
                vol.Required("url"): str,
                vol.Required("username"): str,
                vol.Required("password"): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

class DomologicaOptionsFlow(config_entries.OptionsFlow):
    """Handle Domologica options flow."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        polling_interval = self.config_entry.options.get("polling_interval", 2)
        data_schema = vol.Schema({vol.Required("polling_interval", default=polling_interval): int})
        return self.async_show_form(step_id="init", data_schema=data_schema)
