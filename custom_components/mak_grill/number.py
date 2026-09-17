from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
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
    async_add_entities([GrillSetpointNumber(coordinator, entry, name)])


class GrillSetpointNumber(NumberEntity):
    _attr_has_entity_name = True
    _attr_name = "Setpoint"
    _attr_icon = "mdi:thermometer-lines"
    _attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT
    _attr_native_min_value = 150
    _attr_native_max_value = 500
    _attr_native_step = 5
    _attr_mode = NumberMode.SLIDER

    def __init__(
        self, coordinator: GrillCoordinator, entry: ConfigEntry, grill_name: str
    ) -> None:
        self._coordinator = coordinator
        self._entry = entry
        self._grill_name = grill_name
        self._attr_unique_id = f"{entry.entry_id}_setpoint"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._grill_name,
            manufacturer="MAK Grills",
            model="Pellet Boss WiFi",
        )

    @property
    def native_value(self) -> float:
        return self._coordinator.grill_command.get("setPoint", 175)

    async def async_set_native_value(self, value: float) -> None:
        self._coordinator.grill_command["setPoint"] = int(value)
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        self._coordinator.register_listener(self._handle_update)

    async def async_will_remove_from_hass(self) -> None:
        self._coordinator.remove_listener(self._handle_update)

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()
