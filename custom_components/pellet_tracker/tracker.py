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
    CONF_BAG_SIZE,
    CONF_TANK_SIZE,
    CONF_ACTIVE_STATUSES,
    CONF_POWER_LEVELS,
    CONF_MAX_RATE,
    DEFAULT_BAG_SIZE,
    DEFAULT_MAX_RATE,
    DEFAULT_ALPHA,
    DEFAULT_MIN_RATE_FACTOR,
    DEFAULT_RATE_EWMA_ALPHA,
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
        
        # bag_size_g defines what "100%" means (one full bag)
        # Fall back to legacy tank_size for migrated entries
        bag_size_kg = config.get(CONF_BAG_SIZE) or config.get(CONF_TANK_SIZE, DEFAULT_BAG_SIZE)
        self.bag_size_g = bag_size_kg * 1000
        self.active_statuses = config.get(CONF_ACTIVE_STATUSES, [])
        
        self.current_level_g = self.bag_size_g
        
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
            
            # Minimum rate for levels that would otherwise be 0 (e.g., power level "0").
            # This allows calibration to learn the actual consumption for these levels.
            # Set to ~5% of max rate as an initial estimate that can be adjusted via EWMA.
            min_rate = max_rate * DEFAULT_MIN_RATE_FACTOR
            
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
                    # Apply minimum rate to allow calibration for level 0 or similar
                    self.rates[level_str] = int(max(rate, min_rate))
            else:
                # Fallback to index-based interpolation if levels are not numeric
                # Assumes levels are ordered from lowest to highest
                for i, level in enumerate(active_levels):
                    rate = ((i + 1) / num_levels) * max_rate
                    # Apply minimum rate to allow calibration
                    self.rates[level] = int(max(rate, min_rate))

        self.total_consumed_session_g = 0.0
        self.correction_factors = {}
        self.session_consumption_by_level = {}

        # Rolling average of effective consumption rate (g/h) during active burning.
        # Updated via EWMA every minute tick when stove is active.
        self.avg_consumption_rate: float = 0.0
        # Last known power level — used for predictions when the stove is off.
        self.last_known_power: str | None = None
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
            self.avg_consumption_rate = restored.get("avg_consumption_rate", 0.0)
            self.last_known_power = restored.get("last_known_power", None)

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
            effective_rate = rate * factor
            consumption = effective_rate * elapsed_hours

            # Update rolling average of consumption rate (EWMA)
            if self.avg_consumption_rate <= 0:
                # Bootstrap: first active tick initializes the average
                self.avg_consumption_rate = effective_rate
            else:
                alpha = DEFAULT_RATE_EWMA_ALPHA
                self.avg_consumption_rate = (
                    alpha * effective_rate
                    + (1 - alpha) * self.avg_consumption_rate
                )

            # Track last known power level for off-state predictions
            self.last_known_power = power

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
        """Add a bag of pellets to the tank."""
        _LOGGER.info(
            "Refill (add bag) requested. Current Level: %.2f kg, Bag Size: %.2f kg",
            self.current_level_g / 1000, self.bag_size_g / 1000
        )

        self.current_level_g += self.bag_size_g
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

    @property
    def current_effective_rate(self) -> float | None:
        """Return the current effective consumption rate (g/h) if stove is active, else None."""
        status_state = self.hass.states.get(self.config[CONF_STATUS_ENTITY])
        power_state = self.hass.states.get(self.config[CONF_POWER_ENTITY])

        if not status_state or not power_state:
            return None

        if status_state.state not in self.active_statuses:
            return None

        power = power_state.state
        try:
            power = str(int(float(power)))
        except (ValueError, TypeError):
            pass

        rate = self.rates.get(power)
        if rate is None:
            return None

        factor = self.correction_factors.get(power, 1.0)
        return rate * factor

    @property
    def prediction_rate(self) -> float | None:
        """Return the best available rate (g/h) for time-remaining predictions.

        Priority: current effective rate > rolling average > last-known-power rate.
        """
        # If stove is active, use current rate
        current = self.current_effective_rate
        if current is not None and current > 0:
            return current

        # Stove is off — prefer rolling average if available
        if self.avg_consumption_rate > 0:
            return self.avg_consumption_rate

        # Fallback: use the rate for the last known power level
        if self.last_known_power is not None:
            rate = self.rates.get(self.last_known_power)
            if rate is not None:
                factor = self.correction_factors.get(self.last_known_power, 1.0)
                return rate * factor

        return None

    @property
    def estimated_time_remaining_s(self) -> float | None:
        """Return estimated remaining burn time in seconds, or None if unavailable."""
        rate = self.prediction_rate
        if rate is None or rate <= 0 or self.current_level_g <= 0:
            return None
        hours = self.current_level_g / rate
        return hours * 3600

    @property
    def estimated_empty_datetime(self) -> datetime | None:
        """Return the estimated datetime when pellets will be empty, or None."""
        remaining_s = self.estimated_time_remaining_s
        if remaining_s is None:
            return None
        return dt_util.utcnow() + timedelta(seconds=remaining_s)

    async def _async_save_data(self):
        """Save data to storage."""
        data = {
            "current_level_g": self.current_level_g,
            "rates": self.rates,
            "total_consumed_session_g": self.total_consumed_session_g,
            "correction_factors": self.correction_factors,
            "session_consumption_by_level": self.session_consumption_by_level,
            "avg_consumption_rate": self.avg_consumption_rate,
            "last_known_power": self.last_known_power,
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

    async def async_set_level(self, weight_kg: float, calibrate: bool = False):
        """Manually set the current level by weight in kg."""
        _LOGGER.info("Manual level set requested. Target: %.2f kg, Calibrate: %s", weight_kg, calibrate)
        
        new_level_g = weight_kg * 1000
        
        _LOGGER.info("Current Level: %.2f kg, New Level: %.2f kg", self.current_level_g / 1000, new_level_g / 1000)
        
        # Clamp to 0 (no upper clamp — tank can hold more than one bag)
        if new_level_g < 0:
            new_level_g = 0
            
        if calibrate:
            if self.total_consumed_session_g > 0:
                # Calculate actual consumption implied by this correction
                # session_start = current_level_g + total_consumed_session_g
                # This works even with intermediate refills: refills increase
                # current_level_g but not total_consumed_session_g, so session_start
                # correctly represents total pellets available during the session.
                session_start_g = self.current_level_g + self.total_consumed_session_g
                actual_consumption_g = session_start_g - new_level_g
                
                if actual_consumption_g > 0:
                    await self._async_calibrate(actual_consumption_g)
                else:
                    _LOGGER.warning("Cannot calibrate: Implied consumption is negative or zero.")
            else:
                _LOGGER.debug("Skipping calibration: No session consumption recorded.")
        
        # Always reset session — we're establishing a new known level as ground truth.
        self.total_consumed_session_g = 0
        self.session_consumption_by_level = {}
        
        self.current_level_g = new_level_g
        
        _LOGGER.info("Manual level set complete. New Level: %.2f kg", self.current_level_g / 1000)
        self._notify_listeners()
        await self._async_save_data()
