import logging
import aiohttp

from homeassistant.components.light import (
    LightEntity,
    ColorMode,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Setup luci Domologica."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []

    for element_path, statuses in coordinator.data.items():
        # Consideriamo luce solo se ha switched on/off
        if "isswitchedon" in statuses or "isswitchedoff" in statuses:
            entities.append(
                DomologicaLight(
                    coordinator=coordinator,
                    element_path=element_path,
                    statuses=statuses,
                )
            )

    async_add_entities(entities)


class DomologicaLight(CoordinatorEntity, LightEntity):
    """Entità luce Domologica."""

    def __init__(self, coordinator, element_path, statuses):
        super().__init__(coordinator)

        self.element_path = element_path
        self.statuses = statuses

        self._attr_unique_id = f"domologica_light_{element_path}"

        # Nome: dimmer o light
        if "getdimmer" in statuses:
            self._attr_name = f"Domologica Dimmer {element_path}"
            self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
            self._attr_color_mode = ColorMode.BRIGHTNESS
        else:
            self._attr_name = f"Domologica Light {element_path}"
            self._attr_supported_color_modes = {ColorMode.ONOFF}
            self._attr_color_mode = ColorMode.ONOFF

    @property
    def is_on(self):
        """Stato ON/OFF."""
        return "isswitchedon" in self.coordinator.data.get(self.element_path, {})

    @property
    def brightness(self):
        """Luminosità (0–255)."""
        statuses = self.coordinator.data.get(self.element_path, {})
        if "getdimmer" in statuses:
            try:
                value = int(statuses["getdimmer"])
                return int(value * 255 / 100)
            except Exception:
                return None
        return None

    async def async_turn_on(self, **kwargs):
        """Accende la luce."""
        await self._send_command("switchedon")
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        """Spegne la luce."""
        await self._send_command("switchoff")
        await self.coordinator.async_request_refresh()

    async def _send_command(self, action):
        """Invia comando HTTP a Domologica."""
        url = f"{self.coordinator.url}/elements/{self.element_path}.xml?action={action}"

        auth = aiohttp.BasicAuth(
            self.coordinator.username,
            self.coordinator.password,
        )

        _LOGGER.debug("Domologica call: %s", url)

        async with aiohttp.ClientSession(auth=auth) as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status != 200:
                    raise Exception(
                        f"Domologica HTTP error {resp.status} for {url}"
                    )
