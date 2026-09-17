from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_GRILL_NAME
from .coordinator import GrillCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: GrillCoordinator = hass.data[DOMAIN][entry.entry_id]
    name = entry.data.get(CONF_GRILL_NAME, "MAK Grill")
    async_add_entities([GrillPowerSwitch(coordinator, entry, name)])


class GrillPowerSwitch(SwitchEntity):
    _attr_has_entity_name = True
    _attr_name = "Power"
    _attr_icon = "mdi:power"

    def __init__(
        self, coordinator: GrillCoordinator, entry: ConfigEntry, grill_name: str
    ) -> None:
        self._coordinator = coordinator
        self._entry = entry
        self._grill_name = grill_name
        self._attr_unique_id = f"{entry.entry_id}_power"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._grill_name,
            manufacturer="MAK Grills",
            model="Pellet Boss WiFi",
        )

    @property
    def is_on(self) -> bool:
        return self._coordinator.grill_command.get("power", 1) == 1

    async def async_turn_on(self, **kwargs) -> None:
        reported_pwr = (self._coordinator.grill_state.get("power") or "OFF").upper()
        is_cooldown = self._coordinator.connected and (
            "COOL" in reported_pwr or "CD" in reported_pwr
        )
        if is_cooldown:
            return
        self._coordinator.grill_command["power"] = 1
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        self._coordinator.grill_command["power"] = 0
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        self._coordinator.register_listener(self._handle_update)

    async def async_will_remove_from_hass(self) -> None:
        self._coordinator.remove_listener(self._handle_update)

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()
