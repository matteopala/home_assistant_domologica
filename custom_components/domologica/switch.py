from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
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

        if has_status(elem, "statuson") or has_status(elem, "statusoff"):
            entities.append(DomologicaSwitch(coordinator, entry, str(eid)))

    async_add_entities(entities)


class DomologicaSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, entry, element_id: str):
        super().__init__(coordinator)
        self.entry = entry
        self._element_id = element_id

    @property
    def unique_id(self) -> str:
        return f"{self.entry.entry_id}_switch_{self._element_id}"

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
        if has_status(e, "statuson"):
            return True
        if has_status(e, "statusoff"):
            return False
        return None

    async def async_turn_on(self, **kwargs):
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
