"""Pellet Tracker Logic."""
import logging
from datetime import datetime, timedelta

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_interval, async_track_state_change_event
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    CONF_STATUS_ENTITY,
    CONF_POWER_ENTITY,
    CONF_TANK_SIZE,
    CONF_ACTIVE_STATUSES,
    DEFAULT_TANK_SIZE,
)

_LOGGER = logging.getLogger(__name__)

STORAGE_KEY = f"{DOMAIN}.storage"
STORAGE_VERSION = 1
UPDATE_INTERVAL = timedelta(minutes=1)

DEFAULT_RATES = {
    "0": 0,
    "1": 250,
    "2": 400,
    "3": 600,
    "4": 900,
    "5": 1300,
    "6": 1800,
}

class PelletTracker:
    """Class to manage pellet consumption."""

    def __init__(self, hass: HomeAssistant, config: dict, entry_id: str) -> None:
        self.hass = hass
        self.config = config
        self.entry_id = entry_id
        # Unique storage key per entry to support multiple stoves if needed
        self._store = Store(hass, STORAGE_VERSION, f"{STORAGE_KEY}_{entry_id}")
        
        self.tank_size_g = config.get(CONF_TANK_SIZE, DEFAULT_TANK_SIZE) * 1000
        self.active_statuses = config.get(CONF_ACTIVE_STATUSES, [])
        
        self.current_level_g = self.tank_size_g
        self.rates = DEFAULT_RATES.copy()
        self.total_consumed_session_g = 0.0
        self.last_update = dt_util.utcnow()
        
        self._listeners = []
        self._remove_listeners = []

    async def async_initialize(self):
        """Load data and start tracking."""
        restored = await self._store.async_load()
        if restored:
            self.current_level_g = restored.get("current_level_g", self.current_level_g)
            self.rates = restored.get("rates", self.rates)
            self.total_consumed_session_g = restored.get("total_consumed_session_g", 0.0)
            # Ensure rate keys are strings
            self.rates = {str(k): v for k, v in self.rates.items()}

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
        try:
            # Handle "1.0" or "1"
            power = str(int(float(power_state.state)))
        except (ValueError, TypeError):
            power = "0"

        # Calculate consumption
        consumption = 0.0
        if status in self.active_statuses:
            rate = self.rates.get(power, self.rates.get("1", 250))
            consumption = rate * elapsed_hours
            
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
        # TODO: Implement EWMA calibration here if we have 'amount added'
        self.current_level_g = self.tank_size_g
        self.total_consumed_session_g = 0
        self.last_update = dt_util.utcnow() # Reset timer to avoid jump
        
        await self._async_save_data()
        self._notify_listeners()

    async def _async_save_data(self):
        """Save data to storage."""
        data = {
            "current_level_g": self.current_level_g,
            "rates": self.rates,
            "total_consumed_session_g": self.total_consumed_session_g,
        }
        await self._store.async_save(data)
