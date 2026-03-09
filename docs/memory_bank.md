# Project Memory Bank

## Active Context
- **Current Status**: Weight-based tracking refactor complete.
- **Recent Changes**:
    - **Bag-Based Model**: Replaced fixed "tank size" concept with "bag size". The integration now tracks pellet level by weight internally. A "bag" (default 15 kg) defines what 100% means on the sensor.
    - **Additive Refill**: The "Refill" button (now "Add Bag") adds one bag worth of pellets to the current level instead of resetting to 100%. The internal weight can exceed bag_size_g (e.g. 18 kg after adding 15 kg on top of 3 kg remaining), but the sensor caps at 100%.
    - **Weight-Based Set Level Service**: `set_level` service now accepts weight in kg instead of percentage. The `calibrate` parameter is now required (defaults to `false`).
    - **Calibration Only Via set_level**: Auto-calibration on refill was removed. Calibration only happens when calling `set_level` with `calibrate: true`, providing more reliable ground-truth data.
    - **Config Entry Migration**: V1 → V2 migration renames `tank_size` to `bag_size` in existing config entries.
- **Previous Fixes**:
    - **Minimum Rate for Level 0**: Fixed an issue where power level "0" could never be calibrated. All levels now have a minimum base rate (5% of max rate).
    - **Configuration Updates**: Fixed stale rates being restored from storage. Base rates are always recalculated from config.
- **Implemented Features**:
    - Config Flow (Name, Status, Power, Bag Size).
    - **Custom Power Levels**: User can define specific levels (e.g., "1,2,3,4,5,6,7").
    - **Dynamic Rate Calculation**: Rates are interpolated linearly based on a user-provided Max Rate.
    - **EWMA Auto-Calibration**: Adjusts consumption rates via `set_level` service with `calibrate: true`.
        - **Per-Level Calibration**: Distributes error correction to specific power levels based on their usage contribution.
        - **Minimum Rate Floor**: Ensures all levels (including "0") have a non-zero base rate for calibration.
    - Device Grouping (Entities grouped under a unique device).
    - Virtual Sensor (0-100%, capped — values above bag size still show 100%).
    - **Weight Sensor**: Dedicated sensor showing remaining pellet weight in kg (dashboardable).
    - **Time Remaining Sensor**: Predicts how long the current pellets will last (displayed as a time span via `SensorDeviceClass.DURATION`). Uses an EWMA rolling average of the effective burn rate. When stove is active, prediction uses current burn rate; when off, it falls back to the rolling average or last known power level.
    - **Add Bag Button**: Adds one bag of pellets to the current level.
    - **Service: Set Level**: Manual correction of pellet level in kg, with optional calibration.
    - Persistence (survives restarts).
    - Custom Icon (SVG/PNG) for HACS/GitHub.
    - **Local Brand Images**: Ships `brand/icon.png` inside the integration directory so HA 2026.3+ displays the integration icon natively without relying on the brands CDN.
- **Pending Features**:
    - None.

## System Patterns
- **Tracker Pattern**: `PelletTracker` class acts as a singleton-per-config-entry. It manages its own listeners and notifies entities via a callback list.
- **Device Registry**: Each entry creates a unique Device in the HA registry, allowing multiple instances to coexist cleanly.
- **Storage**: We use `Store` with a delay to avoid thrashing disk on every update, though currently it saves on every consumption tick (might need optimization).
- **Config Flow**: Uses `async_step_params` to inspect the user's chosen entity and offer dynamic choices.
- **Rate Interpolation**: `tracker.py` calculates rates at startup. If levels are numeric, it scales relative to the max value. If strings, it scales by index.

## Tech Stack
- Python 3.13+
- Home Assistant Core (Async)
- Voluptuous (Schema validation)
