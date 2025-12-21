import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import callback
from .const import DOMAIN, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL

class DomologicaFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gestisce il setup iniziale via interfaccia grafica."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            # Crea l'entrata nella configurazione di HA
            return self.async_create_entry(
                title=f"Domologica ({user_input[CONF_HOST]})", 
                data=user_input
            )

        # Campi richiesti all'utente
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
            }),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return DomologicaOptions(config_entry)

class DomologicaOptions(config_entries.OptionsFlow):
    """Permette di cambiare il polling dopo l'installazione."""
    def __init__(self, entry): self.entry = entry
    async def async_step_init(self, user_input=None):
        if user_input is not None: return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(CONF_SCAN_INTERVAL, default=self.entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)): int,
            }),
        )