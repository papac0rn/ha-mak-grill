from __future__ import annotations

import ipaddress
import logging

from aiohttp import web

from homeassistant.components.http import HomeAssistantView
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.network import is_cloud_connection

from .const import DOMAIN, CONF_GRILL_HOST, CONF_GRILL_NAME
from .coordinator import GrillCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor", "number", "switch", "select"]

VIEW_REGISTERED = f"{DOMAIN}_view_registered"
ISSUE_NO_GRILL_ADDRESS = "no_grill_address"


def parse_ip(value: str | None) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    """An IP address, with IPv4-mapped IPv6 (::ffff:a.b.c.d) reduced to IPv4; None if not an address."""
    try:
        ip = ipaddress.ip_address((value or "").strip())
    except ValueError:
        return None
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        return ip.ipv4_mapped
    return ip


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    name = entry.data.get(CONF_GRILL_NAME, "MAK Grill")
    coordinator = GrillCoordinator(hass, name)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # The Create Dashboard button was removed in 1.4.0; drop its leftover entity
    registry = er.async_get(hass)
    if old_button := registry.async_get_entity_id(
        "button", DOMAIN, f"{entry.entry_id}_create_dashboard"
    ):
        registry.async_remove(old_button)

    if parse_ip(entry.data.get(CONF_GRILL_HOST)) is None:
        ir.async_create_issue(
            hass,
            DOMAIN,
            ISSUE_NO_GRILL_ADDRESS,
            is_fixable=False,
            severity=ir.IssueSeverity.ERROR,
            translation_key=ISSUE_NO_GRILL_ADDRESS,
        )
        _LOGGER.error(
            "No grill address is set, so all grill POSTs are refused. Open Settings → Devices & "
            "Services → MAK Grill → ⋮ → Reconfigure and enter the grill's IP address"
        )
    else:
        ir.async_delete_issue(hass, DOMAIN, ISSUE_NO_GRILL_ADDRESS)

    # Register once; the view finds the current entry on every request, so reloads are safe
    if not hass.data.get(VIEW_REGISTERED):
        hass.http.register_view(GrillServiceView())
        hass.data[VIEW_REGISTERED] = True
        _LOGGER.info("Registered /GrillService/Service endpoint")

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    ir.async_delete_issue(hass, DOMAIN, ISSUE_NO_GRILL_ADDRESS)


class GrillServiceView(HomeAssistantView):
    """HTTP endpoint that the Pellet Boss POSTs telemetry to.

    The grill can't send credentials, so the view has no HA auth. Instead it only accepts POSTs
    from the grill address set in the config entry, never through the Nabu Casa cloud, and
    answers everyone else with an empty 403.
    """

    url = "/GrillService/Service"
    name = "mak_grill:service"
    requires_auth = False

    def __init__(self) -> None:
        self._warned: set[str] = set()

    async def post(self, request: web.Request) -> web.Response:
        hass: HomeAssistant = request.app["hass"]
        remote = parse_ip(request.remote)

        coordinator: GrillCoordinator | None = None
        if remote is not None and not is_cloud_connection(hass):
            for entry_id, candidate in hass.data.get(DOMAIN, {}).items():
                entry = hass.config_entries.async_get_entry(entry_id)
                if entry is not None and parse_ip(entry.data.get(CONF_GRILL_HOST)) == remote:
                    coordinator = candidate
                    break

        if coordinator is None:
            source = request.remote or "unknown"
            if source not in self._warned:
                self._warned.add(source)
                _LOGGER.warning(
                    "Refused a POST to /GrillService/Service from %s: not the configured grill "
                    "address. If this is your grill (its IP changed), update it under Settings → "
                    "Devices & Services → MAK Grill → ⋮ → Reconfigure",
                    source,
                )
            return web.Response(status=403)

        data = await request.post()
        form_data = {k: v for k, v in data.items()}

        response_payload = await hass.async_add_executor_job(
            coordinator.process_post, form_data
        )

        coordinator.schedule_timeout_check()

        return web.Response(
            text=response_payload,
            status=200,
            content_type="text/html",
        )
