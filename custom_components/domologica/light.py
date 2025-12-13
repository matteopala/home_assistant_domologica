import logging
from homeassistant.components.light import (
    LightEntity,
    ColorMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from aiohttp import BasicAuth

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
):
    """Setup delle luci Domologica."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities = []

    for element_path, statuses in coordinator.data.items():
        if "isswitchedon" in statuses or "isswitchedoff" in statuses:
            entities.append(
                DomologicaLight(
                    coordinator=coordinator,
                    element_path=element_path,
                    base_url=entry.data["url"],
                    username=entry.data["username"],
                    password=entry.data["password"],
                )
            )

    async_add_entities(entities)


class DomologicaLight(LightEntity):
    """Luce Domologica (on/off o dimmer)."""

    def __init__(
        self,
        coordinator,
        element_path: str,
        base_url: str,
        username: str,
        password: str,
    ):
        self.coordinator = coordinator
        self.element_path = element_path
        self.base_url = base_url.rstrip("/")
        self._auth = BasicAuth(username, password)

        self._attr_unique_id = f"domologica_light_{element_path}"

        if self._has_dimmer:
            self._attr_name = f"Domologica Dimmer {element_path}"
            self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
            self._attr_color_mode = ColorMode.BRIGHTNESS
        else:
            self._attr_name = f"Domologica Light {element_path}"
            self._attr_supported_color_modes = {ColorMode.ONOFF}
            self._attr_color_mode = ColorMode.ONOFF

    @property
    def _has_dimmer(self) -> bool:
        data = self.coordinator.data.get(self.element_path, {})
        return "Getdimmer" in data

    @property
    def is_on(self) -> bool | None:
        data = self.coordinator.data.get(self.element_path)
        if not data:
            return None
        return "isswitchedon" in data

    @property
    def brightness(self) -> int | None:
        if not self._has_dimmer:
            return None

        value = self.coordinator.data[self.element_path].get("Getdimmer")
        if value is None:
            return None

        return int(value * 255 / 100)

    @property
    def extra_state_attributes(self):
        return self.coordinator.data.get(self.element_path, {})

    async def async_turn_on(self, **kwargs):
        """Accende la luce."""
        url = f"{self.base_url}/elements/{self.element_path}.xml?action=switchon"
        session = async_get_clientsession(self.hass)

        _LOGGER.debug("Domologica ON: %s", url)

        async with session.get(url, auth=self._auth) as resp:
            if resp.status != 200:
                raise Exception(f"Errore accensione Domologica {self.element_path}")

        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        """Spegne la luce."""
        url = f"{self.base_url}/elements/{self.element_path}.xml?action=switchoff"
        session = async_get_clientsession(self.hass)

        _LOGGER.debug("Domologica OFF: %s", url)

        async with session.get(url, auth=self._auth) as resp:
            if resp.status != 200:
                raise Exception(f"Errore spegnimento Domologica {self.element_path}")

        await self.coordinator.async_request_refresh()

    async def async_update(self):
        await self.coordinator.async_request_refresh()
