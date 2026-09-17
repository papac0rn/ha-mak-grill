from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_GRILL_NAME, COOK_MODES, ZONE_PROBES
from .coordinator import GrillCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: GrillCoordinator = hass.data[DOMAIN][entry.entry_id]
    name = entry.data.get(CONF_GRILL_NAME, "MAK Grill")
    async_add_entities([
        GrillCookModeSelect(coordinator, entry, name),
        GrillZoneProbeSelect(coordinator, entry, name),
    ])


class GrillSelectBase(SelectEntity):
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: GrillCoordinator, entry: ConfigEntry, grill_name: str
    ) -> None:
        self._coordinator = coordinator
        self._entry = entry
        self._grill_name = grill_name

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._grill_name,
            manufacturer="MAK Grills",
            model="Pellet Boss WiFi",
        )

    async def async_added_to_hass(self) -> None:
        self._coordinator.register_listener(self._handle_update)

    async def async_will_remove_from_hass(self) -> None:
        self._coordinator.remove_listener(self._handle_update)

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()


class GrillCookModeSelect(GrillSelectBase):
    _attr_name = "Cook Mode"
    _attr_icon = "mdi:grill"

    def __init__(
        self, coordinator: GrillCoordinator, entry: ConfigEntry, grill_name: str
    ) -> None:
        super().__init__(coordinator, entry, grill_name)
        self._attr_unique_id = f"{entry.entry_id}_cook_mode"
        self._attr_options = list(COOK_MODES.values())
        self._int_to_str = COOK_MODES
        self._str_to_int = {v: k for k, v in COOK_MODES.items()}

    @property
    def current_option(self) -> str | None:
        val = self._coordinator.grill_command.get("cookMode", 1)
        return self._int_to_str.get(val, self._int_to_str.get(1))

    async def async_select_option(self, option: str) -> None:
        int_val = self._str_to_int.get(option)
        if int_val is not None:
            self._coordinator.mark_user_set("cookMode")
            self._coordinator.grill_command["cookMode"] = int_val
            self.async_write_ha_state()


class GrillZoneProbeSelect(GrillSelectBase):
    _attr_name = "Zone Probe"
    _attr_icon = "mdi:thermometer-probe"

    def __init__(
        self, coordinator: GrillCoordinator, entry: ConfigEntry, grill_name: str
    ) -> None:
        super().__init__(coordinator, entry, grill_name)
        self._attr_unique_id = f"{entry.entry_id}_zone_probe"
        self._attr_options = list(ZONE_PROBES.values())
        self._int_to_str = ZONE_PROBES
        self._str_to_int = {v: k for k, v in ZONE_PROBES.items()}

    @property
    def current_option(self) -> str | None:
        val = self._coordinator.grill_command.get("zoneProbe", 1)
        return self._int_to_str.get(val, self._int_to_str.get(1))

    async def async_select_option(self, option: str) -> None:
        int_val = self._str_to_int.get(option)
        if int_val is not None:
            self._coordinator.mark_user_set("zoneProbe")
            self._coordinator.grill_command["zoneProbe"] = int_val
            self.async_write_ha_state()
