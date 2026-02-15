"""Sensor platform for Pellet Tracker."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfMass, UnitOfTime
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
    async_add_entities([
        PelletTrackerSensor(tracker),
        PelletWeightSensor(tracker),
        PelletTimeRemainingSensor(tracker),
    ])

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
        """Return the state of the sensor.

        Percentage is based on bag_size_g (one full bag = 100%).
        Values above bag_size_g (e.g. after adding a bag on top of
        remaining pellets) are capped at 100%.
        """
        if self._tracker.bag_size_g <= 0:
            return 0
        pct = (self._tracker.current_level_g / self._tracker.bag_size_g) * 100
        return max(0, min(100, int(pct)))

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        return {
            "remaining_kg": round(self._tracker.current_level_g / 1000, 2),
            "current_rates": self._tracker.rates,
            "session_consumed_kg": round(self._tracker.total_consumed_session_g / 1000, 2),
        }


class PelletWeightSensor(SensorEntity):
    """Sensor showing the remaining pellet weight in kg."""

    _attr_has_entity_name = True
    _attr_name = "Pellet Weight"
    _attr_device_class = SensorDeviceClass.WEIGHT
    _attr_native_unit_of_measurement = UnitOfMass.KILOGRAMS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:weight-kilogram"

    def __init__(self, tracker: PelletTracker) -> None:
        """Initialize the sensor."""
        self._tracker = tracker
        self._attr_unique_id = f"{tracker.entry_id}_weight"
        self._attr_device_info = tracker.device_info

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        self.async_on_remove(
            self._tracker.add_listener(self.async_write_ha_state)
        )

    @property
    def native_value(self) -> float:
        """Return the remaining weight in kg."""
        return round(self._tracker.current_level_g / 1000, 2)


class PelletTimeRemainingSensor(SensorEntity):
    """Sensor showing estimated time remaining for pellets."""

    _attr_has_entity_name = True
    _attr_name = "Time Remaining"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_icon = "mdi:timer-sand"
    _attr_suggested_display_precision = 0

    def __init__(self, tracker: PelletTracker) -> None:
        """Initialize the sensor."""
        self._tracker = tracker
        self._attr_unique_id = f"{tracker.entry_id}_time_remaining"
        self._attr_device_info = tracker.device_info

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        self.async_on_remove(
            self._tracker.add_listener(self.async_write_ha_state)
        )

    @property
    def native_value(self) -> float | None:
        """Return the estimated time remaining in seconds."""
        return self._tracker.estimated_time_remaining_s

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra attributes with prediction details."""
        attrs: dict = {}
        rate = self._tracker.prediction_rate
        if rate is not None:
            attrs["burn_rate_kg_h"] = round(rate / 1000, 3)
        if self._tracker.avg_consumption_rate > 0:
            attrs["avg_burn_rate_kg_h"] = round(
                self._tracker.avg_consumption_rate / 1000, 3
            )
        empty_dt = self._tracker.estimated_empty_datetime
        if empty_dt is not None:
            attrs["estimated_empty_at"] = empty_dt.isoformat()
        if self._tracker.last_known_power is not None:
            attrs["last_known_power"] = self._tracker.last_known_power
        return attrs
