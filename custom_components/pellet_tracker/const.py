"""Constants for the Pellet Tracker integration."""

DOMAIN = "pellet_tracker"

# Configuration Constants
CONF_STATUS_ENTITY = "status_entity"
CONF_POWER_ENTITY = "power_entity"
CONF_TANK_SIZE = "tank_size"
CONF_ACTIVE_STATUSES = "active_statuses"
CONF_POWER_LEVELS = "power_levels"
CONF_MAX_RATE = "max_rate"

# Defaults
DEFAULT_TANK_SIZE = 15.0  # kg
DEFAULT_ACTIVE_STATUSES = ["WORK", "START"]
DEFAULT_MAX_RATE = 1.8  # kg/h
DEFAULT_ALPHA = 0.15  # Learning rate for EWMA
DEFAULT_MIN_RATE_FACTOR = 0.05  # Minimum rate as fraction of max rate (5%)
