from __future__ import annotations

import time

from homeassistant.components.switch import SwitchEntity, SwitchDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN
from .utils import async_command, normalize_entity_name


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.data or {}
    enabled = getattr(coordinator, "enabled_elements", set())
    info_map = getattr(coordinator, "element_info", {})

    entities = []
    for eid, st in data.items():
        if enabled and eid not in enabled:
            continue

        info = info_map.get(eid, {})
        kind = info.get("kind")

        # switch:
        # - prese riconosciute da metadati (SocketElement)
        # - eventuali switch legacy con statuson/statusoff
        if kind in ("switch_outlet", "switch") or ("statuson" in st or "statusoff" in st):
            entities.append(DomologicaSwitch(coordinator, entry, eid))

    async_add_entities(entities)


class DomologicaSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, entry, element_id: str):
        super().__init__(coordinator)
        self.entry = entry
        self._element_id = element_id

        self._opt_until = 0.0
        self._opt_is_on: bool | None = None

        info = getattr(self.coordinator, "element_info", {}).get(self._element_id, {})
        if info.get("kind") == "switch_outlet":
            self._attr_device_class = SwitchDeviceClass.OUTLET

    @property
    def unique_id(self) -> str:
        return f"{self.entry.entry_id}_switch_{self._element_id}"

    @property
    def name(self) -> str:
        info = getattr(self.coordinator, "element_info", {}).get(self._element_id, {})
        api_name = info.get("name")
        alias = getattr(self.coordinator, "aliases", {}).get(self._element_id) or api_name
        return normalize_entity_name(self._element_id, alias)

    @property
    def device_info(self) -> DeviceInfo:
        info = getattr(self.coordinator, "element_info", {}).get(self._element_id, {})
        api_name = info.get("name")
        alias = getattr(self.coordinator, "aliases", {}).get(self._element_id) or api_name
        return DeviceInfo(
            identifiers={(DOMAIN, self._element_id)},
            name=f"Domologica {normalize_entity_name(self._element_id, alias)}",
            manufacturer="Domologica",
        )

    def _optimistic_active(self) -> bool:
        return time.monotonic() < self._opt_until

    @property
    def is_on(self) -> bool | None:
        if self._optimistic_active() and self._opt_is_on is not None:
            return self._opt_is_on

        st = (self.coordinator.data or {}).get(self._element_id, {})
        # prese/socket e molte luci usano isswitchedon/off
        if "isswitchedon" in st:
            return True
        if "isswitchedoff" in st:
            return False
        # alcuni vecchi switch possono usare statuson/off
        if "statuson" in st:
            return True
        if "statusoff" in st:
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

        self.coordinator.apply_optimistic(
            self._element_id,
            updates={"isswitchedon": True},
            remove={"isswitchedoff"},
        )

        self._opt_is_on = True
        self._opt_until = time.monotonic() + 2.5
        self.async_write_ha_state()

        self.coordinator.schedule_refresh_turbo()

    async def async_turn_off(self, **kwargs):
        await async_command(
            self.hass,
            self.coordinator.base_url,
            self._element_id,
            "switchoff",
            self.coordinator.username,
            self.coordinator.password,
        )

        self.coordinator.apply_optimistic(
            self._element_id,
            updates={"isswitchedoff": True},
            remove={"isswitchedon"},
        )

        self._opt_is_on = False
        self._opt_until = time.monotonic() + 2.5
        self.async_write_ha_state()

        self.coordinator.schedule_refresh_turbo()
