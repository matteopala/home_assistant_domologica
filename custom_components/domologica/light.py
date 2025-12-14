from __future__ import annotations

from homeassistant.components.light import LightEntity, ColorMode
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN
from .utils import (
    async_command,
    async_set_dimmer,
    element_by_id,
    has_status,
    read_value,
    normalize_entity_name,
)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    root = coordinator.data

    entities = []
    for elem in root.findall("ElementStatus"):
        eid = elem.findtext("ElementPath")
        if not eid:
            continue

        # euristica: luce se ha ON/OFF o dimmer
        if (
            has_status(elem, "isswitchedon")
            or has_status(elem, "isswitchedoff")
            or has_status(elem, "getdimmer")
        ):
            entities.append(DomologicaLight(coordinator, entry, str(eid)))

    async_add_entities(entities)


class DomologicaLight(CoordinatorEntity, LightEntity):
    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}

    def __init__(self, coordinator, entry, element_id: str):
        super().__init__(coordinator)
        self.entry = entry
        self._element_id = element_id

    @property
    def unique_id(self) -> str:
        return f"{self.entry.entry_id}_light_{self._element_id}"

    @property
    def name(self) -> str:
        return normalize_entity_name(self._element_id)

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._element_id)},
            name=f"Domologica Element {self._element_id}",
            manufacturer="Domologica",
        )

    @property
    def is_on(self) -> bool | None:
        e = element_by_id(self.coordinator.data, self._element_id)
        if e is None:
            return None
        if has_status(e, "isswitchedon"):
            return True
        if has_status(e, "isswitchedoff"):
            return False
        return None

    @property
    def brightness(self) -> int | None:
        e = element_by_id(self.coordinator.data, self._element_id)
        if e is None:
            return None
        dim = read_value(e, "getdimmer")
        if dim is None:
            return None
        try:
            # Domologica 0–100 → HA 0–255
            return int(float(dim) * 255 / 100)
        except ValueError:
            return None

    async def async_turn_on(self, **kwargs):
        if "brightness" in kwargs:
            ha_brightness = int(kwargs["brightness"])
            domo_value = int(ha_brightness * 100 / 255)
            await async_set_dimmer(
                self.hass,
                self.coordinator.base_url,
                self._element_id,
                domo_value,
                self.coordinator.username,
                self.coordinator.password,
            )
        else:
            await async_command(
                self.hass,
                self.coordinator.base_url,
                self._element_id,
                "switchon",
                self.coordinator.username,
                self.coordinator.password,
            )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await async_command(
            self.hass,
            self.coordinator.base_url,
            self._element_id,
            "switchoff",
            self.coordinator.username,
            self.coordinator.password,
        )
        await self.coordinator.async_request_refresh()
