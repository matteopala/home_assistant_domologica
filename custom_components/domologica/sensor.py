from __future__ import annotations

from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import Entity, DeviceInfo

from .const import DOMAIN
from .utils import normalize_entity_name


_MAX_STATE_LEN = 255


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.data or {}
    enabled = getattr(coordinator, "enabled_elements", set())

    entities = []
    for eid, st in data.items():
        if enabled and eid not in enabled:
            continue

        for sid, val in st.items():
            # sensori = solo status con value (noi salviamo True per flag)
            if val is True:
                continue
            entities.append(DomologicaSensor(coordinator, entry, eid, sid))

    async_add_entities(entities)


class DomologicaSensor(CoordinatorEntity, Entity):
    def __init__(self, coordinator, entry, element_id: str, status_id: str):
        super().__init__(coordinator)
        self.entry = entry
        self._element_id = element_id
        self._status_id = status_id

        self._last_full_value: str | None = None
        self._is_truncated: bool = False

    @property
    def unique_id(self) -> str:
        safe = self._status_id.replace(" ", "_")
        return f"{self.entry.entry_id}_sensor_{self._element_id}_{safe}"

    @property
    def name(self) -> str:
        alias = getattr(self.coordinator, "aliases", {}).get(self._element_id)
        return normalize_entity_name(self._element_id, alias, self._status_id)

    @property
    def device_info(self) -> DeviceInfo:
        alias = getattr(self.coordinator, "aliases", {}).get(self._element_id)
        return DeviceInfo(
            identifiers={(DOMAIN, self._element_id)},
            name=f"Domologica {normalize_entity_name(self._element_id, alias)}",
            manufacturer="Domologica",
        )

    def _compute_state_and_attrs(self, raw: object) -> tuple[object | None, dict]:
        # raw può essere stringa/numero/etc (nel nostro parse_statuses è quasi sempre str)
        if raw is None or raw is True:
            self._last_full_value = None
            self._is_truncated = False
            return None, {}

        s = str(raw)
        if len(s) <= _MAX_STATE_LEN:
            self._last_full_value = None
            self._is_truncated = False
            return s, {}

        # Troppo lungo: stato breve + valore completo negli attributi
        self._last_full_value = s
        self._is_truncated = True

        # stato “short” stabile e leggibile (evita unknown e evita spam log)
        short = s[: (_MAX_STATE_LEN - 1)] + "…"
        attrs = {
            "truncated": True,
            "full_value": s,
            "full_length": len(s),
        }
        return short, attrs

    @property
    def state(self):
        st = (self.coordinator.data or {}).get(self._element_id, {})
        raw = st.get(self._status_id)
        state, _ = self._compute_state_and_attrs(raw)
        return state

    @property
    def extra_state_attributes(self):
        st = (self.coordinator.data or {}).get(self._element_id, {})
        raw = st.get(self._status_id)
        _, attrs = self._compute_state_and_attrs(raw)
        return attrs
