from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow

from .const import DOMAIN, DEFAULT_NAME, CONF_GRILL_NAME


class MakGrillConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=user_input[CONF_GRILL_NAME],
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_GRILL_NAME, default=DEFAULT_NAME): str,
                }
            ),
        )
