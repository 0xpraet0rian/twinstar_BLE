"""Config flow for Twinstar LED."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.core import HomeAssistant

from .const import CONF_PRIMARY_MAC, CONF_SLAVE_MAC, DEFAULT_NAME, DOMAIN
from .protocol import is_valid_mac, normalize_mac

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PRIMARY_MAC): str,
        vol.Optional(CONF_SLAVE_MAC, default=""): str,
    }
)


def _normalize_or_empty(value: str) -> str | None:
    value = value.strip()
    if not value:
        return None
    return normalize_mac(value)


async def async_validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, str]:
    """Validate user input."""
    primary = normalize_mac(data[CONF_PRIMARY_MAC])
    if not is_valid_mac(primary):
        raise ValueError("invalid_mac")

    slave_raw = data.get(CONF_SLAVE_MAC, "") or ""
    slave = _normalize_or_empty(slave_raw)

    if slave is not None:
        if not is_valid_mac(slave):
            raise ValueError("invalid_mac")
        if slave == primary:
            raise ValueError("same_mac")

    return {
        CONF_PRIMARY_MAC: primary,
        CONF_SLAVE_MAC: slave or "",
    }


class TwinstarConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Twinstar LED."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                validated = await async_validate_input(self.hass, user_input)
            except ValueError as err:
                err_code = err.args[0] if err.args else "unknown"
                if err_code == "invalid_mac":
                    errors["base"] = "invalid_mac"
                elif err_code == "same_mac":
                    errors["base"] = "same_mac"
                else:
                    errors["base"] = "unknown"
            else:
                primary = validated[CONF_PRIMARY_MAC]
                await self.async_set_unique_id(primary.lower().replace(":", ""))
                self._abort_if_unique_id_configured()

                title = f"{DEFAULT_NAME} {primary}"
                return self.async_create_entry(
                    title=title,
                    data={
                        CONF_PRIMARY_MAC: primary,
                        CONF_SLAVE_MAC: validated.get(CONF_SLAVE_MAC) or "",
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                STEP_USER_DATA_SCHEMA,
                user_input or {},
            ),
            errors=errors,
        )
