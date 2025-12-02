# Project Memory Bank

## Active Context
- **Current Status**: Feature-complete MVP.
- **Recent Fixes**:
    - **Minimum Rate for Level 0**: Fixed an issue where power level "0" (or any level interpolating to 0) could never be calibrated because `rate * correction_factor = 0` always equals 0. Now, all levels have a minimum base rate (5% of max rate by default), allowing EWMA calibration to converge towards actual consumption.
    - **Configuration Updates**: Fixed an issue where updating power levels in the config would not take effect because stale rates were being restored from storage. Now, base rates are always recalculated from config, while learned correction factors are preserved.
- **Implemented Features**:
    - Config Flow (Name, Status, Power, Tank Size).
    - **Custom Power Levels**: User can define specific levels (e.g., "1,2,3,4,5,6,7").
    - **Dynamic Rate Calculation**: Rates are interpolated linearly based on a user-provided Max Rate.
    - **EWMA Auto-Calibration**: Automatically adjusts consumption rates based on refill behavior.
        - **Per-Level Calibration**: Distributes error correction to specific power levels based on their usage contribution.
        - **Minimum Rate Floor**: Ensures all levels (including "0") have a non-zero base rate for calibration.
    - Device Grouping (Entities grouped under a unique device).
    - Virtual Sensor (0-100%).
    - Refill Button.
    - Persistence (survives restarts).
    - Custom Icon (SVG/PNG) for HACS/GitHub.
    - **Service: Set Level**: Allows manual correction of the pellet level (e.g., `pellet_tracker.set_level`).
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
