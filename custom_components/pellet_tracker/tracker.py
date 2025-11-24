"""Pellet Tracker Logic."""
import logging
from datetime import datetime, timedelta

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.event import async_track_time_interval, async_track_state_change_event
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

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
    DEFAULT_ALPHA,
)

_LOGGER = logging.getLogger(__name__)

STORAGE_KEY = f"{DOMAIN}.storage"
STORAGE_VERSION = 1
UPDATE_INTERVAL = timedelta(minutes=1)

# Default rates are now calculated dynamically
# Unit: grams per hour (g/h)

class PelletTracker:
    """Class to manage pellet consumption."""

    def __init__(self, hass: HomeAssistant, config: dict, entry_id: str, name: str) -> None:
        self.hass = hass
        self.config = config
        self.entry_id = entry_id
        self.name = name
        # Unique storage key per entry to support multiple stoves if needed
        self._store = Store(hass, STORAGE_VERSION, f"{STORAGE_KEY}_{entry_id}")
        
        self.tank_size_g = config.get(CONF_TANK_SIZE, DEFAULT_TANK_SIZE) * 1000
        self.active_statuses = config.get(CONF_ACTIVE_STATUSES, [])
        
        self.current_level_g = self.tank_size_g
        
        # Initialize rates based on configured power levels
        power_levels = config.get(CONF_POWER_LEVELS)
        if not power_levels:
            # Default to 1-5 if not specified
            power_levels = ["1", "2", "3", "4", "5"]

        self.rates = {}
        
        # We allow "0" to be an active level if the user explicitly includes it in power_levels
        active_levels = [l for l in power_levels]
            
        # Calculate rates for active levels using linear interpolation
        num_levels = len(active_levels)
        if num_levels > 0:
            # Get max from config (stored in kg/h, convert to g/h)
            max_rate = config.get(CONF_MAX_RATE, DEFAULT_MAX_RATE) * 1000
            
            # Try to parse levels as numbers to find the max level
            try:
                numeric_levels = [float(l) for l in active_levels]
                max_level_val = max(numeric_levels)
                is_numeric = True
            except ValueError:
                is_numeric = False
            
            if is_numeric and max_level_val > 0:
                # Interpolate based on numeric value relative to max level
                for level_str, level_val in zip(active_levels, numeric_levels):
                    rate = (level_val / max_level_val) * max_rate
                    self.rates[level_str] = int(rate)
            else:
                # Fallback to index-based interpolation if levels are not numeric
                # Assumes levels are ordered from lowest to highest
                for i, level in enumerate(active_levels):
                    rate = ((i + 1) / num_levels) * max_rate
                    self.rates[level] = int(rate)

        self.total_consumed_session_g = 0.0
        self.correction_factors = {}
        self.session_consumption_by_level = {}
        self.last_update = dt_util.utcnow()
        
        self._listeners = []
        self._remove_listeners = []

    async def async_initialize(self):
        """Load data and start tracking."""
        restored = await self._store.async_load()
        if restored:
            self.current_level_g = restored.get("current_level_g", self.current_level_g)
            
            # NOTE: We do NOT restore 'rates' from storage.
            # 'rates' are the BASE consumption rates derived purely from the configuration (Power Levels & Max Rate).
            # If we restored them, we would ignore configuration changes (like adding a new level or changing Max Rate).
            # The actual "calibration" is stored in 'correction_factors', which IS restored below.
            
            self.total_consumed_session_g = restored.get("total_consumed_session_g", 0.0)
            self.correction_factors = restored.get("correction_factors", {})
            self.session_consumption_by_level = restored.get("session_consumption_by_level", {})
            
            # Ensure keys are strings
            self.correction_factors = {str(k): v for k, v in self.correction_factors.items()}
            self.session_consumption_by_level = {str(k): v for k, v in self.session_consumption_by_level.items()}

            _LOGGER.debug(
                "Restored state: Level=%.1fkg, Calibration Factors=%s. Base Rates (Config)=%s", 
                self.current_level_g / 1000, 
                self.correction_factors,
                self.rates
            )

        # Start tracking
        self._remove_listeners.append(
            async_track_time_interval(self.hass, self._async_update_consumption, UPDATE_INTERVAL)
        )
        
        self._remove_listeners.append(
            async_track_state_change_event(
                self.hass, 
                [self.config[CONF_STATUS_ENTITY], self.config[CONF_POWER_ENTITY]], 
                self._async_handle_state_change
            )
        )

    def close(self):
        """Cleanup listeners."""
        for remove in self._remove_listeners:
            remove()
        self._remove_listeners.clear()

    def add_listener(self, callback_func):
        """Add a listener for state updates."""
        self._listeners.append(callback_func)
        return lambda: self._listeners.remove(callback_func)

    def _notify_listeners(self):
        """Notify all listeners."""
        for listener in self._listeners:
            listener()

    async def _async_handle_state_change(self, event):
        """Handle state changes immediately."""
        await self._async_update_consumption()

    async def _async_update_consumption(self, now=None):
        """Calculate consumption."""
        current_time = dt_util.utcnow()
        elapsed_hours = (current_time - self.last_update).total_seconds() / 3600.0
        self.last_update = current_time
        
        if elapsed_hours <= 0:
            return

        # Get current status and power
        status_state = self.hass.states.get(self.config[CONF_STATUS_ENTITY])
        power_state = self.hass.states.get(self.config[CONF_POWER_ENTITY])
        
        if not status_state or not power_state:
            return
            
        status = status_state.state
        
        power = power_state.state
        # Try to normalize numeric power to match keys like "1", "2"
        try:
            power = str(int(float(power)))
        except (ValueError, TypeError):
            pass # Keep original string if not numeric

        # Calculate consumption
        consumption = 0.0
        if status in self.active_statuses:
            rate = self.rates.get(power)
            if rate is None:
                _LOGGER.warning(
                    "Stove is active (Status: %s) but Power Level '%s' is not configured in %s. "
                    "Assuming 0 consumption. Please update configuration.",
                    status, power, CONF_POWER_LEVELS
                )
                # Fallback logic
                if "1" in self.rates:
                    rate = self.rates["1"]
                elif self.rates:
                    # Use the first available rate if "1" is not found
                    rate = next(iter(self.rates.values()))
                else:
                    rate = 0
            
            # Apply correction factor for this specific level
            factor = self.correction_factors.get(power, 1.0)
            consumption = (rate * factor) * elapsed_hours
            
            # Track consumption per level for calibration
            if consumption > 0:
                current_level_consumption = self.session_consumption_by_level.get(power, 0.0)
                self.session_consumption_by_level[power] = current_level_consumption + consumption
            
        if consumption > 0:
            self.current_level_g -= consumption
            self.total_consumed_session_g += consumption
            
            # Clamp to 0
            if self.current_level_g < 0:
                self.current_level_g = 0
                
            self._notify_listeners()
            await self._async_save_data()

    async def async_refill(self):
        """Refill the tank to full."""
        _LOGGER.info("Refill requested. Current Level: %.2f kg", self.current_level_g / 1000)

        # EWMA Auto-Calibration (Per-Level)
        # We only calibrate if the tank is nearly empty (< 10% remaining)
        threshold = self.tank_size_g * 0.1
        
        if self.current_level_g < threshold and self.total_consumed_session_g > 0:
            # Assume we consumed the entire tank (Actual = Tank Size)
            await self._async_calibrate(self.tank_size_g)
        else:
            _LOGGER.debug(
                "Skipping calibration during refill. Level (%.2f kg) >= Threshold (%.2f kg) or No Consumption (%.2f kg)",
                self.current_level_g / 1000,
                threshold / 1000,
                self.total_consumed_session_g / 1000
            )

        self.current_level_g = self.tank_size_g
        self.total_consumed_session_g = 0
        self.session_consumption_by_level = {} # Reset session tracking
        self.last_update = dt_util.utcnow()
        
        _LOGGER.info("Refill complete. New Level: %.2f kg", self.current_level_g / 1000)
        await self._async_save_data()
        self._notify_listeners()

    async def _async_calibrate(self, actual_consumption_g: float):
        """Run EWMA calibration based on actual consumption."""
        estimated_consumption = self.total_consumed_session_g
        
        if estimated_consumption <= 0:
            return

        _LOGGER.debug("Starting Calibration. Current Factors: %s", self.correction_factors)

        error_ratio = actual_consumption_g / estimated_consumption
        
        # Limit the error ratio to avoid wild swings
        error_ratio = max(0.5, min(error_ratio, 2.0))
        
        _LOGGER.info(
            "Auto-Calibrating Rates. Estimated: %.2f kg, Actual: %.2f kg. Ratio: %.3f",
            estimated_consumption / 1000,
            actual_consumption_g / 1000,
            error_ratio
        )
        
        # Distribute error to levels based on their contribution
        for level, level_consumption in self.session_consumption_by_level.items():
            weight = level_consumption / estimated_consumption
            
            old_factor = self.correction_factors.get(level, 1.0)
            # Update factor: New = Old * (1 + Alpha * Weight * (Error - 1))
            new_factor = old_factor * (1 + DEFAULT_ALPHA * weight * (error_ratio - 1))
            
            self.correction_factors[level] = new_factor
            
            _LOGGER.debug(
                "Calibrating Level %s: Weight=%.2f, Old Factor=%.3f, New Factor=%.3f",
                level, weight, old_factor, new_factor
            )
            
        _LOGGER.debug("Calibration Complete. Updated Factors: %s", self.correction_factors)
        
        effective_rates = {
            level: int(rate * self.correction_factors.get(level, 1.0))
            for level, rate in self.rates.items()
        }
        _LOGGER.debug("New Effective Rates (g/h): %s", effective_rates)

    async def _async_save_data(self):
        """Save data to storage."""
        data = {
            "current_level_g": self.current_level_g,
            "rates": self.rates,
            "total_consumed_session_g": self.total_consumed_session_g,
            "correction_factors": self.correction_factors,
            "session_consumption_by_level": self.session_consumption_by_level,
        }
        await self._store.async_save(data)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.entry_id)},
            name=self.name,
            manufacturer="Pellet Tracker",
            model="Virtual Sensor",
        )

    async def async_set_level(self, level_kg: float, calibrate: bool = False):
        """Manually set the current level."""
        _LOGGER.info("Manual level set requested. Target: %.2f kg, Calibrate: %s", level_kg, calibrate)
        _LOGGER.info("Current Level: %.2f kg", self.current_level_g / 1000)

        new_level_g = level_kg * 1000
        
        # Clamp
        if new_level_g > self.tank_size_g:
            new_level_g = self.tank_size_g
        if new_level_g < 0:
            new_level_g = 0
            
        if calibrate:
            if self.total_consumed_session_g > 0:
                # Calculate actual consumption implied by this correction
                # Start_Level = current_level_g + total_consumed_session_g
                # Actual_Consumed = Start_Level - new_level_g
                # Actual_Consumed = (current_level_g + total_consumed_session_g) - new_level_g
                
                actual_consumption_g = (self.current_level_g + self.total_consumed_session_g) - new_level_g
                
                if actual_consumption_g > 0:
                    await self._async_calibrate(actual_consumption_g)
                    
                    # Reset session tracking after calibration
                    self.total_consumed_session_g = 0
                    self.session_consumption_by_level = {}
                else:
                    _LOGGER.warning("Cannot calibrate: Implied consumption is negative or zero.")
            else:
                _LOGGER.debug("Skipping calibration: No session consumption recorded.")
        
        # If we are setting a new level (even without calibration), we should probably reset the session
        # to establish a new ground truth, otherwise future calibrations will be skewed by the pre-correction error.
        # However, if calibrate=False, maybe the user just wants to tweak it slightly?
        # Let's reset session only if we calibrated OR if the change is significant?
        # For simplicity and correctness, setting a manual level establishes a new known state.
        # We should reset the session counters so the next period starts fresh from this known level.
        self.total_consumed_session_g = 0
        self.session_consumption_by_level = {}
        
        self.current_level_g = new_level_g
        
        _LOGGER.info("Manual level set complete. New Level: %.2f kg", self.current_level_g / 1000)
        self._notify_listeners()
        await self._async_save_data()
