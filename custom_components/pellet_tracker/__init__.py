"""The Pellet Tracker integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .tracker import PelletTracker

# List the platforms that you want to support.
PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BUTTON]

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Pellet Tracker component."""
    
    async def handle_set_level(call):
        entry_id = call.data.get("entry_id")
        level_pct = call.data.get("level")
        calibrate = call.data.get("calibrate", False)
        
        if DOMAIN in hass.data and entry_id in hass.data[DOMAIN]:
            tracker = hass.data[DOMAIN][entry_id]
            await tracker.async_set_level(level_pct, calibrate)
            
    hass.services.async_register(DOMAIN, "set_level", handle_set_level)
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Pellet Tracker from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Merge data and options
    config = {**entry.data, **entry.options}
    
    tracker = PelletTracker(hass, config, entry.entry_id, entry.title)
    await tracker.async_initialize()
    
    hass.data[DOMAIN][entry.entry_id] = tracker
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Listen for options updates
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        tracker = hass.data[DOMAIN].pop(entry.entry_id)
        tracker.close()

    return unload_ok
