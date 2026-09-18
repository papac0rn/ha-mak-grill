from __future__ import annotations

import logging

from aiohttp import web

from homeassistant.components.http import HomeAssistantView
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_GRILL_NAME
from .coordinator import GrillCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor", "number", "switch", "select", "button"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    name = entry.data.get(CONF_GRILL_NAME, "MAK Grill")
    coordinator = GrillCoordinator(hass, name)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    hass.http.register_view(GrillServiceView(coordinator))
    _LOGGER.info("Registered /GrillService/Service endpoint for '%s'", name)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


class GrillServiceView(HomeAssistantView):
    """Unauthenticated HTTP endpoint that the Pellet Boss POSTs telemetry to."""

    url = "/GrillService/Service"
    name = "mak_grill:service"
    requires_auth = False

    def __init__(self, coordinator: GrillCoordinator) -> None:
        self._coordinator = coordinator

    async def post(self, request: web.Request) -> web.Response:
        data = await request.post()
        form_data = {k: v for k, v in data.items()}

        response_payload = await request.app["hass"].async_add_executor_job(
            self._coordinator.process_post, form_data
        )

        self._coordinator.schedule_timeout_check()

        return web.Response(
            text=response_payload,
            status=200,
            content_type="text/html",
        )
