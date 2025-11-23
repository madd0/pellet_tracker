"""Button platform for Pellet Tracker."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .tracker import PelletTracker

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Pellet Tracker button."""
    tracker: PelletTracker = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PelletRefillButton(tracker)])

class PelletRefillButton(ButtonEntity):
    """Representation of a Pellet Refill Button."""

    _attr_has_entity_name = True
    _attr_name = "Refill Tank"
    _attr_icon = "mdi:autorenew"

    def __init__(self, tracker: PelletTracker) -> None:
        """Initialize the button."""
        self._tracker = tracker
        self._attr_unique_id = f"{tracker.entry_id}_refill"
        self._attr_device_info = tracker.device_info

    async def async_press(self) -> None:
        """Handle the button press."""
        await self._tracker.async_refill()
