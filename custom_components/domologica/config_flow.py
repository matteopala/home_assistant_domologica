import aiohttp
import voluptuous as vol
from homeassistant import config_entries

DOMAIN = "domologica"

DATA_SCHEMA = vol.Schema({
    vol.Required("domologica_url"): str,
    vol.Required("username"): str,
    vol.Required("password"): str
})

class DomologicaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gestione del config flow per Domologica."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Step iniziale dell’utente."""
        errors = {}

        if user_input is not None:
            # Test connessione async con aiohttp
            try:
                auth = aiohttp.BasicAuth(user_input["username"], user_input["password"])
                async with aiohttp.ClientSession(auth=auth) as session:
                    async with session.get(user_input["domologica_url"], timeout=10) as resp:
                        if resp.status != 200:
                            errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "cannot_connect"

            if not errors:
                return self.async_create_entry(title="Domologica", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors
        )
