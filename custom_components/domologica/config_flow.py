import voluptuous as vol
from homeassistant import config_entries

from .const import DOMAIN

class DomologicaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gestione della configurazione dell'integrazione Domologica."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Step iniziale della configurazione da interfaccia utente."""

        if user_input is None:
            # Mostra il form iniziale
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema({
                    vol.Required("url"): str,
                    vol.Required("username"): str,
                    vol.Required("password"): str,
                    vol.Required("polling_interval", default=2): int
                })
            )

        # Salva i dati inseriti
        return self.async_create_entry(title="Domologica", data=user_input)
