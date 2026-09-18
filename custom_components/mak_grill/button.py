from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_GRILL_NAME
from .coordinator import GrillCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: GrillCoordinator = hass.data[DOMAIN][entry.entry_id]
    name = entry.data.get(CONF_GRILL_NAME, "MAK Grill")
    async_add_entities([CreateDashboardButton(coordinator, entry, name)])


def _entity_id(registry: er.EntityRegistry, entry_id: str, platform: str, key: str) -> str | None:
    unique_id = f"{entry_id}_{key}"
    return registry.async_get_entity_id(platform, DOMAIN, unique_id)


def _build_dashboard_config(
    registry: er.EntityRegistry, name: str, entry_id: str
) -> dict:
    def eid(platform: str, key: str) -> str:
        found = _entity_id(registry, entry_id, platform, key)
        if found:
            return found
        slug = name.lower().replace(" ", "_").replace("-", "_")
        fallback_map = {
            ("sensor", "temp"): f"sensor.{slug}_temperature",
            ("sensor", "probe1"): f"sensor.{slug}_probe_1",
            ("sensor", "probe2"): f"sensor.{slug}_probe_2",
            ("sensor", "probe3"): f"sensor.{slug}_probe_3",
            ("sensor", "power_state"): f"sensor.{slug}_power_state",
            ("sensor", "flags"): f"sensor.{slug}_flags",
            ("sensor", "grill_id"): f"sensor.{slug}_grill_id",
            ("sensor", "last_seen"): f"sensor.{slug}_last_seen",
            ("sensor", "post_count"): f"sensor.{slug}_post_count",
            ("binary_sensor", "connected"): f"binary_sensor.{slug}_connected",
            ("binary_sensor", "flameout"): f"binary_sensor.{slug}_flameout",
            ("binary_sensor", "at_setpoint"): f"binary_sensor.{slug}_at_setpoint",
            ("number", "setpoint"): f"number.{slug}_setpoint",
            ("switch", "power"): f"switch.{slug}_power",
            ("select", "cook_mode"): f"select.{slug}_cook_mode",
            ("select", "zone_probe"): f"select.{slug}_zone_probe",
        }
        return fallback_map.get((platform, key), f"{platform}.{slug}_{key}")

    return {
        "views": [
            {
                "title": name,
                "path": "overview",
                "cards": [
                    {
                        "type": "gauge",
                        "entity": eid("sensor", "temp"),
                        "name": "Pit Temperature",
                        "unit": "°F",
                        "needle": True,
                        "min": 0,
                        "max": 600,
                        "segments": [
                            {"from": 0, "color": "#43a047"},
                            {"from": 200, "color": "#ffa600"},
                            {"from": 350, "color": "#db4437"},
                            {"from": 450, "color": "#9c27b0"},
                        ],
                    },
                    {
                        "type": "entities",
                        "title": "Controls",
                        "entities": [
                            {"entity": eid("number", "setpoint"), "name": "Setpoint"},
                            {"entity": eid("switch", "power"), "name": "Power"},
                            {"entity": eid("select", "cook_mode"), "name": "Cook Mode"},
                            {"entity": eid("select", "zone_probe"), "name": "Zone Probe"},
                        ],
                    },
                    {
                        "type": "entities",
                        "title": "Probes",
                        "entities": [
                            {"entity": eid("sensor", "probe1"), "name": "Probe 1"},
                            {"entity": eid("sensor", "probe2"), "name": "Probe 2"},
                            {"entity": eid("sensor", "probe3"), "name": "Probe 3"},
                            {"entity": eid("number", "setpoint"), "name": "Setpoint"},
                        ],
                    },
                    {
                        "type": "history-graph",
                        "title": "Cook History",
                        "hours_to_show": 12,
                        "entities": [
                            {"entity": eid("sensor", "temp"), "name": "Pit Temp"},
                            {"entity": eid("sensor", "probe1"), "name": "Probe 1"},
                            {"entity": eid("sensor", "probe2"), "name": "Probe 2"},
                            {"entity": eid("sensor", "probe3"), "name": "Probe 3"},
                            {"entity": eid("number", "setpoint"), "name": "Setpoint"},
                        ],
                    },
                    {
                        "type": "entities",
                        "title": "Status",
                        "entities": [
                            {"entity": eid("binary_sensor", "connected"), "name": "Connected"},
                            {"entity": eid("sensor", "power_state"), "name": "Power State"},
                            {"entity": eid("sensor", "grill_id"), "name": "Grill ID"},
                        ],
                    },
                    {
                        "type": "entities",
                        "title": "Safety & Diagnostics",
                        "entities": [
                            {"entity": eid("binary_sensor", "flameout"), "name": "Flameout"},
                            {"entity": eid("binary_sensor", "at_setpoint"), "name": "At Setpoint"},
                            {"entity": eid("sensor", "flags"), "name": "Flags"},
                            {"entity": eid("sensor", "last_seen"), "name": "Last Seen"},
                            {"entity": eid("sensor", "post_count"), "name": "Post Count"},
                        ],
                    },
                ],
            }
        ]
    }


class CreateDashboardButton(ButtonEntity):
    _attr_has_entity_name = True
    _attr_name = "Create Dashboard"
    _attr_icon = "mdi:view-dashboard-edit"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self, coordinator: GrillCoordinator, entry: ConfigEntry, grill_name: str
    ) -> None:
        self._coordinator = coordinator
        self._entry = entry
        self._grill_name = grill_name
        self._attr_unique_id = f"{entry.entry_id}_create_dashboard"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._grill_name,
            manufacturer="MAK Grills",
            model="Pellet Boss WiFi",
        )

    async def async_press(self) -> None:
        hass = self.hass
        url_path = "mak-grill"

        lovelace_data = hass.data.get("lovelace")
        if lovelace_data is None:
            _LOGGER.error("Lovelace component not loaded")
            return

        dashboards = lovelace_data.dashboards
        collection = lovelace_data.dashboard_collection
        if collection is None:
            _LOGGER.error("Cannot create dashboard: no dashboard collection")
            return

        if url_path in dashboards:
            _LOGGER.info(
                "Dashboard '%s' already exists — removing old one before recreating",
                url_path,
            )
            try:
                old_item = None
                for item in collection.async_items():
                    if item.get("url_path") == url_path:
                        old_item = item
                        break
                if old_item and old_item.get("id"):
                    await collection.async_delete_item(old_item["id"])
                    _LOGGER.info("Removed old '%s' dashboard", url_path)
            except Exception:
                _LOGGER.warning(
                    "Could not remove old dashboard — will overwrite config instead"
                )

        dashboards = lovelace_data.dashboards
        if url_path not in dashboards:
            await collection.async_create_item({
                "url_path": url_path,
                "title": self._grill_name,
                "icon": "mdi:grill",
                "require_admin": False,
                "show_in_sidebar": True,
            })
            _LOGGER.info("Created '%s' dashboard", self._grill_name)

        dashboards = lovelace_data.dashboards
        dashboard = dashboards.get(url_path)
        if dashboard is None:
            _LOGGER.error("Dashboard '%s' not found after creation", url_path)
            return

        registry = er.async_get(hass)
        config = _build_dashboard_config(registry, self._grill_name, self._entry.entry_id)
        await dashboard.async_save(config)
        _LOGGER.info(
            "Saved %s dashboard with %d cards — open it from the sidebar",
            self._grill_name,
            len(config["views"][0]["cards"]),
        )
