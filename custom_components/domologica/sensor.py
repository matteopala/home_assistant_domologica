from __future__ import annotations

from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import Entity, DeviceInfo

from .const import DOMAIN
from .utils import (
    element_by_id,
    list_status_ids_with_value,
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

        for sid in list_status_ids_with_value(elem):
            entities.append(
                DomologicaSensor(coordinator, entry, str(eid), sid)
            )

    async_add_entities(entities)


class DomologicaSensor(CoordinatorEntity, Entity):
    def __init__(self, coordinator, entry, element_id: str, status_id: str):
        super().__init__(coordinator)
        self.entry = entry
        self._element_id = element_id
        self._status_id = status_id

    @property
    def unique_id(self) -> str:
        safe = self._status_id.replace(" ", "_")
        return f"{self.entry.entry_id}_sensor_{self._element_id}_{safe}"

    @property
    def name(self) -> str:
        return normalize_entity_name(self._element_id, None, self._status_id)

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._element_id)},
            name=f"Domologica Element {self._element_id}",
            manufacturer="Domologica",
        )

    @property
    def state(self):
        e = element_by_id(self.coordinator.data, self._element_id)
        if e is None:
            return None
        return read_value(e, self._status_id)
