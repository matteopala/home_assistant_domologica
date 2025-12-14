from __future__ import annotations

from homeassistant.components.cover import CoverEntity, CoverDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN
from .utils import async_command, element_by_id, has_status, normalize_entity_name


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    root = coordinator.data

    entities = []
    for elem in root.findall("ElementStatus"):
        eid = elem.findtext("ElementPath")
        if not eid:
            continue

        # euristica tapparella: up switched / down switched
        if has_status(elem, "up switched") or has_status(elem, "down switched"):
            entities.append(DomologicaCover(coordinator, entry, str(eid)))

    async_add_entities(entities)


class DomologicaCover(CoordinatorEntity, CoverEntity):
    _attr_device_class = CoverDeviceClass.SHUTTER

    def __init__(self, coordinator, entry, element_id: str):
        super().__init__(coordinator)
        self.entry = entry
        self._element_id = element_id

    @property
    def unique_id(self) -> str:
        return f"{self.entry.entry_id}_cover_{self._element_id}"

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
    def is_closed(self) -> bool | None:
        e = element_by_id(self.coordinator.data, self._element_id)
        if e is None:
            return None

        # Nota: qui stiamo deducendo lo stato dalla presenza degli status.
        # Se sono "eventi momentanei", questo potrebbe non riflettere la posizione reale.
        if has_status(e, "down switched"):
            return True
        if has_status(e, "up switched"):
            return False
        return None

    async def async_open_cover(self, **kwargs):
        await async_command(
            self.hass,
            self.coordinator.base_url,
            self._element_id,
            "turnup",
            self.coordinator.username,
            self.coordinator.password,
        )
        await self.coordinator.async_request_refresh()

    async def async_close_cover(self, **kwargs):
        await async_command(
            self.hass,
            self.coordinator.base_url,
            self._element_id,
            "turndown",
            self.coordinator.username,
            self.coordinator.password,
        )
        await self.coordinator.async_request_refresh()
