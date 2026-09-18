from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_GRILL_NAME
from .coordinator import GrillCoordinator

TEMPERATURE_SENSORS = [
    ("temp", "Temperature", "mdi:thermometer"),
    ("probe1", "Probe 1", "mdi:thermometer-probe"),
    ("probe2", "Probe 2", "mdi:thermometer-probe"),
    ("probe3", "Probe 3", "mdi:thermometer-probe"),
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: GrillCoordinator = hass.data[DOMAIN][entry.entry_id]
    name = entry.data.get(CONF_GRILL_NAME, "MAK Grill")

    entities: list[SensorEntity] = []

    for key, label, icon in TEMPERATURE_SENSORS:
        entities.append(GrillTempSensor(coordinator, entry, name, key, label, icon))

    entities.append(GrillPowerStateSensor(coordinator, entry, name))
    entities.append(GrillFlagsSensor(coordinator, entry, name))
    entities.append(GrillIdSensor(coordinator, entry, name))
    entities.append(GrillLastSeenSensor(coordinator, entry, name))
    entities.append(GrillPostCountSensor(coordinator, entry, name))

    async_add_entities(entities)


class GrillSensorBase(SensorEntity):
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


class GrillTempSensor(GrillSensorBase):
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: GrillCoordinator,
        entry: ConfigEntry,
        grill_name: str,
        key: str,
        label: str,
        icon: str,
    ) -> None:
        super().__init__(coordinator, entry, grill_name)
        self._key = key
        self._attr_name = label
        self._attr_icon = icon
        self._attr_unique_id = f"{entry.entry_id}_{key}"

    @property
    def native_value(self) -> float:
        val = self._coordinator.grill_state.get(self._key)
        return val if val is not None else 0.0


class GrillPowerStateSensor(GrillSensorBase):
    _attr_name = "Power State"
    _attr_icon = "mdi:power"

    def __init__(
        self, coordinator: GrillCoordinator, entry: ConfigEntry, grill_name: str
    ) -> None:
        super().__init__(coordinator, entry, grill_name)
        self._attr_unique_id = f"{entry.entry_id}_power_state"

    @property
    def native_value(self) -> str:
        return self._coordinator.grill_state.get("power", "OFF")


class GrillFlagsSensor(GrillSensorBase):
    _attr_name = "Flags"
    _attr_icon = "mdi:flag-variant"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self, coordinator: GrillCoordinator, entry: ConfigEntry, grill_name: str
    ) -> None:
        super().__init__(coordinator, entry, grill_name)
        self._attr_unique_id = f"{entry.entry_id}_flags"

    @property
    def native_value(self) -> str:
        return self._coordinator.grill_state.get("flags", "")


class GrillIdSensor(GrillSensorBase):
    _attr_name = "Grill ID"
    _attr_icon = "mdi:identifier"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self, coordinator: GrillCoordinator, entry: ConfigEntry, grill_name: str
    ) -> None:
        super().__init__(coordinator, entry, grill_name)
        self._attr_unique_id = f"{entry.entry_id}_grill_id"

    @property
    def native_value(self) -> str:
        return self._coordinator.grill_state.get("grill_id", "Unknown")


class GrillLastSeenSensor(GrillSensorBase):
    _attr_name = "Last Seen"
    _attr_icon = "mdi:clock-check-outline"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self, coordinator: GrillCoordinator, entry: ConfigEntry, grill_name: str
    ) -> None:
        super().__init__(coordinator, entry, grill_name)
        self._attr_unique_id = f"{entry.entry_id}_last_seen"

    @property
    def native_value(self) -> datetime | None:
        return self._coordinator.last_seen_utc


class GrillPostCountSensor(GrillSensorBase):
    _attr_name = "Post Count"
    _attr_icon = "mdi:counter"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self, coordinator: GrillCoordinator, entry: ConfigEntry, grill_name: str
    ) -> None:
        super().__init__(coordinator, entry, grill_name)
        self._attr_unique_id = f"{entry.entry_id}_post_count"

    @property
    def native_value(self) -> int:
        return self._coordinator.post_count
