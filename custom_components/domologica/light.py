from __future__ import annotations

import time

from homeassistant.components.light import LightEntity, ColorMode
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN
from .utils import async_command, async_set_dimmer, normalize_entity_name


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
        kind = info.get("kind")  # 'light', 'light_dimmer', 'cover', 'switch_outlet', ...

        # NON creare luci per prese/switch/outlet
        if kind in ("switch_outlet", "switch", "cover"):
            continue

        # luce dimmer o luce on/off:
        if kind in ("light", "light_dimmer"):
            entities.append(DomologicaLight(coordinator, entry, eid))
            continue

        # fallback (se metadati non presenti): solo se vedo getdimmer/pwm o flag tipici luce
        if (
            "getdimmer" in st
            or "pwmValue" in st
            or "isswitchedon" in st
            or "isswitchedoff" in st
        ):
            # attenzione: potrebbe essere una presa se non abbiamo metadati.
            # preferiamo NON crearla qui per evitare piattaforma sbagliata.
            # quindi creiamo solo se dimmerabile (getdimmer/pwm).
            if "getdimmer" in st or "pwmValue" in st:
                entities.append(DomologicaLight(coordinator, entry, eid))

    async_add_entities(entities)


class DomologicaLight(CoordinatorEntity, LightEntity):
    def __init__(self, coordinator, entry, element_id: str):
        super().__init__(coordinator)
        self.entry = entry
        self._element_id = element_id

        self._opt_until = 0.0
        self._opt_is_on: bool | None = None
        self._opt_brightness: int | None = None

        info = getattr(self.coordinator, "element_info", {}).get(self._element_id, {})
        kind = info.get("kind")

        st = (self.coordinator.data or {}).get(self._element_id, {})
        self._is_dimmer = (kind == "light_dimmer") or ("getdimmer" in st)

        if self._is_dimmer:
            self._attr_color_mode = ColorMode.BRIGHTNESS
            self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
        else:
            self._attr_color_mode = ColorMode.ONOFF
            self._attr_supported_color_modes = {ColorMode.ONOFF}

    @property
    def unique_id(self) -> str:
        return f"{self.entry.entry_id}_light_{self._element_id}"

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
        if "isswitchedon" in st:
            return True
        if "isswitchedoff" in st:
            return False
        return None

    @property
    def brightness(self) -> int | None:
        if not self._is_dimmer:
            return None

        if self._optimistic_active() and self._opt_brightness is not None:
            return self._opt_brightness

        st = (self.coordinator.data or {}).get(self._element_id, {})
        dim = st.get("getdimmer")
        if dim is None or dim is True:
            return None
        try:
            return int(float(str(dim)) * 255 / 100)
        except ValueError:
            return None

    async def async_turn_on(self, **kwargs):
        if self._is_dimmer and "brightness" in kwargs:
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

            self.coordinator.apply_optimistic(
                self._element_id,
                updates={"getdimmer": str(domo_value), "isswitchedon": True},
                remove={"isswitchedoff"},
            )

            self._opt_is_on = True
            self._opt_brightness = ha_brightness
            self._opt_until = time.monotonic() + 2.5
            self.async_write_ha_state()

        else:
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
            self._opt_brightness = self.brightness
            self._opt_until = time.monotonic() + 2.5
            self.async_write_ha_state()

        # ✅ non blocca
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

        # ✅ non blocca
        self.coordinator.schedule_refresh_turbo()
