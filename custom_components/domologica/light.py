import logging
import aiohttp

from homeassistant.components.light import (
    LightEntity,
    ColorMode,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Setup luci Domologica."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []

    for element_path, statuses in coordinator.data.items():
        entities.append(
            DomologicaLight(
                coordinator=coordinator,
                element_path=element_path,
                statuses=statuses,
            )
        )

    async_add_entities(entities)


class DomologicaLight(CoordinatorEntity, LightEntity):
    """Entità Light Domologica."""

    def __init__(self, coordinator, element_path, statuses):
        super().__init__(coordinator)

        self.element_path = element_path
        self._statuses = statuses

        self._attr_unique_id = f"domologica_light_{element_path}"
        self._attr_name = f"Domologica Light {element_path}"

        # Capabilities
        if "getdimmer" in statuses:
            self._attr_color_mode = ColorMode.BRIGHTNESS
            self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
        else:
            self._attr_color_mode = ColorMode.ONOFF
            self._attr_supported_color_modes = {ColorMode.ONOFF}

    @property
    def is_on(self):
        return "isswitchedon" in self.coordinator.data.get(self.element_path, {})

    @property
    def brightness(self):
        statuses = self.coordinator.data.get(self.element_path, {})
        dimmer = statuses.get("getdimmer")
        if dimmer is None:
            return None
        try:
            return int(dimmer) * 255 // 100
        except ValueError:
            return None

    async def async_turn_on(self, **kwargs):
        if ColorMode.BRIGHTNESS in self.supported_color_modes and "brightness" in kwargs:
            percent = int(kwargs["brightness"] * 100 / 255)
            await self._send_command(f"setdimmer&value={percent}")
        else:
            await self._send_command("switchedon")

        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self._send_command("switchoff")
        await self.coordinator.async_request_refresh()

    async def _send_command(self, action: str):
        """Invia comando HTTP al device Domologica."""
        session = async_get_clientsession(self.hass)

        url = f"http://192.168.5.2/elements/{self.element_path}.xml?action={action}"

        auth = aiohttp.BasicAuth(
            self.coordinator.username,
            self.coordinator.password,
        )

        try:
            async with session.get(
                url,
                auth=auth,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    raise Exception(f"HTTP {resp.status}")

        except aiohttp.ClientError as err:
            _LOGGER.error(
                "Errore comando Domologica %s (%s): %s",
                self.element_path,
                action,
                err,
            )
            raise
