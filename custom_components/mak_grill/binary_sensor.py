from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
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

    async_add_entities([
        GrillConnectedSensor(coordinator, entry, name),
        GrillFlameoutSensor(coordinator, entry, name),
        GrillAtSetpointSensor(coordinator, entry, name),
    ])


class GrillBinarySensorBase(BinarySensorEntity):
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


class GrillConnectedSensor(GrillBinarySensorBase):
    _attr_name = "Connected"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_icon = "mdi:wifi"

    def __init__(
        self, coordinator: GrillCoordinator, entry: ConfigEntry, grill_name: str
    ) -> None:
        super().__init__(coordinator, entry, grill_name)
        self._attr_unique_id = f"{entry.entry_id}_connected"

    @property
    def is_on(self) -> bool:
        return self._coordinator.connected


class GrillFlameoutSensor(GrillBinarySensorBase):
    _attr_name = "Flameout"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_icon = "mdi:fire-alert"

    def __init__(
        self, coordinator: GrillCoordinator, entry: ConfigEntry, grill_name: str
    ) -> None:
        super().__init__(coordinator, entry, grill_name)
        self._attr_unique_id = f"{entry.entry_id}_flameout"

    @property
    def is_on(self) -> bool:
        return self._coordinator.flameout_triggered


class GrillAtSetpointSensor(GrillBinarySensorBase):
    _attr_name = "At Setpoint"
    _attr_icon = "mdi:thermometer-check"

    def __init__(
        self, coordinator: GrillCoordinator, entry: ConfigEntry, grill_name: str
    ) -> None:
        super().__init__(coordinator, entry, grill_name)
        self._attr_unique_id = f"{entry.entry_id}_at_setpoint"

    @property
    def is_on(self) -> bool:
        return self._coordinator.at_setpoint
