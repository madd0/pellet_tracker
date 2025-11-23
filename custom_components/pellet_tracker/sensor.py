"""Sensor platform for Pellet Tracker."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .tracker import PelletTracker

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Pellet Tracker sensor."""
    tracker: PelletTracker = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PelletTrackerSensor(tracker)])

class PelletTrackerSensor(SensorEntity):
    """Representation of a Pellet Tracker Sensor."""

    _attr_has_entity_name = True
    _attr_name = "Pellet Level"
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:fire-circle"
    _attr_unique_id = "pellet_level"

    def __init__(self, tracker: PelletTracker) -> None:
        """Initialize the sensor."""
        self._tracker = tracker
        self._attr_unique_id = f"{tracker.entry_id}_level"
        self._attr_device_info = tracker.device_info

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        self.async_on_remove(
            self._tracker.add_listener(self.async_write_ha_state)
        )

    @property
    def native_value(self) -> int:
        """Return the state of the sensor."""
        if self._tracker.tank_size_g <= 0:
            return 0
        pct = (self._tracker.current_level_g / self._tracker.tank_size_g) * 100
        return max(0, min(100, int(pct)))

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        return {
            "remaining_kg": round(self._tracker.current_level_g / 1000, 2),
            "current_rates": self._tracker.rates,
            "session_consumed_kg": round(self._tracker.total_consumed_session_g / 1000, 2),
        }
