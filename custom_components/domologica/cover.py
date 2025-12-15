from __future__ import annotations

import time

from homeassistant.components.cover import CoverEntity, CoverDeviceClass, CoverEntityFeature
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

        # cover se status lo indica O metadati dicono cover
        if ("up switched" in st) or ("down switched" in st) or (kind == "cover"):
            entities.append(DomologicaCover(coordinator, entry, eid))

    async_add_entities(entities)


class DomologicaCover(CoordinatorEntity, CoverEntity):
    _attr_device_class = CoverDeviceClass.SHUTTER
    _attr_supported_features = CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP

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
    def is_closed(self) -> bool | None:
        if self._optimistic_active() and self._opt_closed is not None:
            return self._opt_closed

        st = (self.coordinator.data or {}).get(self._element_id, {})

        # Se hai status "up switched/down switched" li usiamo
        if "down switched" in st:
            return True
        if "up switched" in st:
            return False

        # Altrimenti, per ShutterElement spesso ci sono isgoingup/isgoingdown:
        # non indica "chiusa/aperta", ma almeno evita stati incoerenti.
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

        self.coordinator.apply_optimistic(
            self._element_id,
            updates={"up switched": True},
            remove={"down switched"},
        )

        self._opt_closed = False
        self._opt_until = time.monotonic() + 2.5
        self.async_write_ha_state()

        self.coordinator.schedule_refresh_turbo()

    async def async_close_cover(self, **kwargs):
        await async_command(
            self.hass,
            self.coordinator.base_url,
            self._element_id,
            "turndown",
            self.coordinator.username,
            self.coordinator.password,
        )

        self.coordinator.apply_optimistic(
            self._element_id,
            updates={"down switched": True},
            remove={"up switched"},
        )

        self._opt_closed = True
        self._opt_until = time.monotonic() + 2.5
        self.async_write_ha_state()

        self.coordinator.schedule_refresh_turbo()

    async def async_stop_cover(self, **kwargs):
        await async_command(
            self.hass,
            self.coordinator.base_url,
            self._element_id,
            "stop",
            self.coordinator.username,
            self.coordinator.password,
        )

        self._opt_until = time.monotonic() + 1.5
        self.async_write_ha_state()

        self.coordinator.schedule_refresh_turbo()
