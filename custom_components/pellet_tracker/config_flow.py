"""Config flow for Pellet Tracker integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_STATUS_ENTITY,
    CONF_POWER_ENTITY,
    CONF_TANK_SIZE,
    CONF_ACTIVE_STATUSES,
    CONF_POWER_LEVELS,
    CONF_MAX_RATE,
    DEFAULT_TANK_SIZE,
    DEFAULT_MAX_RATE,
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
                    vol.Required(CONF_NAME, default="Pellet Stove"): str,
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
            if isinstance(user_input[CONF_ACTIVE_STATUSES], str):
                user_input[CONF_ACTIVE_STATUSES] = [
                    s.strip() for s in user_input[CONF_ACTIVE_STATUSES].split(",")
                ]

            # Process power levels
            if isinstance(user_input.get(CONF_POWER_LEVELS), str):
                user_input[CONF_POWER_LEVELS] = [
                    s.strip() for s in user_input[CONF_POWER_LEVELS].split(",")
                ]
            
            data = {**self.data, **user_input}
            return self.async_create_entry(title=self.data[CONF_NAME], data=data)

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
                ),
                vol.Required(
                    CONF_POWER_LEVELS, default="1, 2, 3, 4, 5"
                ): str,
                vol.Required(CONF_MAX_RATE, default=DEFAULT_MAX_RATE): vol.Coerce(float),
            })
        else:
            # Fallback to text input
            schema = vol.Schema({
                vol.Required(CONF_TANK_SIZE, default=DEFAULT_TANK_SIZE): vol.Coerce(float),
                vol.Required(
                    CONF_ACTIVE_STATUSES, default=", ".join(default_statuses)
                ): str,
                vol.Required(
                    CONF_POWER_LEVELS, default="1, 2, 3, 4, 5"
                ): str,
                vol.Required(CONF_MAX_RATE, default=DEFAULT_MAX_RATE): vol.Coerce(float),
            })

        return self.async_show_form(
            step_id="params",
            data_schema=schema
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Pellet Tracker."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            # Process the active statuses string into a list if it's a string
            if isinstance(user_input[CONF_ACTIVE_STATUSES], str):
                user_input[CONF_ACTIVE_STATUSES] = [
                    s.strip() for s in user_input[CONF_ACTIVE_STATUSES].split(",")
                ]

            # Process power levels
            if isinstance(user_input.get(CONF_POWER_LEVELS), str):
                user_input[CONF_POWER_LEVELS] = [
                    s.strip() for s in user_input[CONF_POWER_LEVELS].split(",")
                ]
                
            return self.async_create_entry(title="", data=user_input)

        # Get current config (merged data and options)
        config = {**self.config_entry.data, **self.config_entry.options}
        
        # Try to get options from the status entity
        status_entity = config[CONF_STATUS_ENTITY]
        state = self.hass.states.get(status_entity)
        options = []
        if state and "options" in state.attributes:
            options = state.attributes["options"]
            
        current_statuses = config.get(CONF_ACTIVE_STATUSES, [])
        current_power_levels = config.get(CONF_POWER_LEVELS, [])
        if isinstance(current_power_levels, list):
            current_power_levels = ", ".join(current_power_levels)
            
        if options:
            # Filter defaults to only those present in options
            valid_defaults = [s for s in current_statuses if s in options]
            
            schema = vol.Schema({
                vol.Required(CONF_TANK_SIZE, default=config.get(CONF_TANK_SIZE, DEFAULT_TANK_SIZE)): vol.Coerce(float),
                vol.Required(
                    CONF_ACTIVE_STATUSES, default=valid_defaults
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=options, multiple=True)
                ),
                vol.Required(
                    CONF_POWER_LEVELS, default=current_power_levels
                ): str,
                vol.Required(CONF_MAX_RATE, default=config.get(CONF_MAX_RATE, DEFAULT_MAX_RATE)): vol.Coerce(float),
            })
        else:
            if isinstance(current_statuses, list):
                current_statuses = ", ".join(current_statuses)
                
            schema = vol.Schema({
                vol.Required(CONF_TANK_SIZE, default=config.get(CONF_TANK_SIZE, DEFAULT_TANK_SIZE)): vol.Coerce(float),
                vol.Required(
                    CONF_ACTIVE_STATUSES, default=current_statuses
                ): str,
                vol.Required(
                    CONF_POWER_LEVELS, default=current_power_levels
                ): str,
                vol.Required(CONF_MAX_RATE, default=config.get(CONF_MAX_RATE, DEFAULT_MAX_RATE)): vol.Coerce(float),
            })

        return self.async_show_form(
            step_id="init",
            data_schema=schema
        )
