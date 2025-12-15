from __future__ import annotations

import time

from homeassistant.components.cover import CoverEntity, CoverDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN
from .utils import async_command, normalize_entity_name


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.data or {}

    entities = []
    for eid, st in data.items():
        if "up switched" in st or "down switched" in st:
            entities.append(DomologicaCover(coordinator, entry, eid))

    async_add_entities(entities)


class DomologicaCover(CoordinatorEntity, CoverEntity):
    _attr_device_class = CoverDeviceClass.SHUTTER

    def __init__(self, coordinator, entry, element_id: str):
        super().__init__(coordinator)
        self.entry = entry
        self._element_id = element_id

        self._opt_until = 0.0
        self._opt_closed: bool | None = None

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

    def _optimistic_active(self) -> bool:
        return time.monotonic() < self._opt_until

    @property
    def is_closed(self) -> bool | None:
        if self._optimistic_active() and self._opt_closed is not None:
            return self._opt_closed

        st = (self.coordinator.data or {}).get(self._element_id, {})
        if "down switched" in st:
            return True
        if "up switched" in st:
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

        # ✅ aggiorna subito cache (così anche sensori/status correlati seguono)
        self.coordinator.apply_optimistic(
            self._element_id,
            updates={"up switched": True},
            remove={"down switched"},
        )

        self._opt_closed = False
        self._opt_until = time.monotonic() + 2.5
        self.async_write_ha_state()

        await self.coordinator.async_schedule_refresh()

    async def async_close_cover(self, **kwargs):
        await async_command(
            self.hass,
            self.coordinator.base_url,
            self._element_id,
            "turndown",
            self.coordinator.username,
            self.coordinator.password,
        )

        # ✅ aggiorna subito cache (così anche sensori/status correlati seguono)
        self.coordinator.apply_optimistic(
            self._element_id,
            updates={"down switched": True},
            remove={"up switched"},
        )

        self._opt_closed = True
        self._opt_until = time.monotonic() + 2.5
        self.async_write_ha_state()

        await self.coordinator.async_schedule_refresh()
