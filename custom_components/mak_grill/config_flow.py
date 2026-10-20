from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow

from .const import DOMAIN, DEFAULT_NAME, CONF_GRILL_HOST, CONF_GRILL_NAME


def _valid_ip(value: str) -> str | None:
    """The address as text if it is a valid IP address, else None."""
    from . import parse_ip

    ip = parse_ip(value)
    return str(ip) if ip is not None else None


class MakGrillConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            host = _valid_ip(user_input[CONF_GRILL_HOST])
            if host is None:
                errors[CONF_GRILL_HOST] = "invalid_ip"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_GRILL_NAME],
                    data={**user_input, CONF_GRILL_HOST: host},
                )

        user_input = user_input or {}
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_GRILL_NAME, default=user_input.get(CONF_GRILL_NAME, DEFAULT_NAME)
                    ): str,
                    vol.Required(
                        CONF_GRILL_HOST, default=user_input.get(CONF_GRILL_HOST, "")
                    ): str,
                }
            ),
            errors=errors,
        )

    async def async_step_reconfigure(self, user_input=None):
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            host = _valid_ip(user_input[CONF_GRILL_HOST])
            if host is None:
                errors[CONF_GRILL_HOST] = "invalid_ip"
            else:
                return self.async_update_reload_and_abort(
                    entry, data_updates={CONF_GRILL_HOST: host}
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_GRILL_HOST,
                        default=(user_input or entry.data).get(CONF_GRILL_HOST, ""),
                    ): str,
                }
            ),
            errors=errors,
        )
