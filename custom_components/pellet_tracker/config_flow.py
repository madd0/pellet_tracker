"""Config flow for Pellet Tracker integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_STATUS_ENTITY,
    CONF_POWER_ENTITY,
    CONF_TANK_SIZE,
    CONF_ACTIVE_STATUSES,
    DEFAULT_TANK_SIZE,
)

_LOGGER = logging.getLogger(__name__)

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Pellet Tracker."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            self.data = user_input
            return await self.async_step_params()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_STATUS_ENTITY): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="sensor")
                    ),
                    vol.Required(CONF_POWER_ENTITY): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="sensor")
                    ),
                }
            ),
        )

    async def async_step_params(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the parameters step."""
        if user_input is not None:
            # Process the active statuses string into a list if it's a string
            # (It will be a list if using SelectSelector, string if using text input)
            if isinstance(user_input[CONF_ACTIVE_STATUSES], str):
                user_input[CONF_ACTIVE_STATUSES] = [
                    s.strip() for s in user_input[CONF_ACTIVE_STATUSES].split(",")
                ]
            
            data = {**self.data, **user_input}
            return self.async_create_entry(title="Pellet Tracker", data=data)

        # Try to get options from the status entity
        status_entity = self.data[CONF_STATUS_ENTITY]
        state = self.hass.states.get(status_entity)
        options = []
        if state and "options" in state.attributes:
            options = state.attributes["options"]
        
        # Default active statuses
        default_statuses = ["WORK", "START"]
        
        if options:
            # If we have options, use a multi-select dropdown
            # Filter defaults to only those present in options to avoid validation errors
            valid_defaults = [s for s in default_statuses if s in options]
            
            schema = vol.Schema({
                vol.Required(CONF_TANK_SIZE, default=DEFAULT_TANK_SIZE): vol.Coerce(float),
                vol.Required(
                    CONF_ACTIVE_STATUSES, default=valid_defaults
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=options, multiple=True)
                )
            })
        else:
            # Fallback to text input
            schema = vol.Schema({
                vol.Required(CONF_TANK_SIZE, default=DEFAULT_TANK_SIZE): vol.Coerce(float),
                vol.Required(
                    CONF_ACTIVE_STATUSES, default=", ".join(default_statuses)
                ): str,
            })

        return self.async_show_form(
            step_id="params",
            data_schema=schema
        )
