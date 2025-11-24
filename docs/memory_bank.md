# Project Memory Bank

## Active Context
- **Current Status**: Feature-complete MVP.
- **Implemented Features**:
    - Config Flow (Name, Status, Power, Tank Size).
    - **Custom Power Levels**: User can define specific levels (e.g., "1,2,3,4,5,6,7").
    - **Dynamic Rate Calculation**: Rates are interpolated linearly based on a user-provided Max Rate.
    - **EWMA Auto-Calibration**: Automatically adjusts consumption rates based on refill behavior.
        - **Per-Level Calibration**: Distributes error correction to specific power levels based on their usage contribution.
    - Device Grouping (Entities grouped under a unique device).
    - Virtual Sensor (0-100%).
    - Refill Button.
    - Persistence (survives restarts).
    - Custom Icon (SVG/PNG) for HACS/GitHub.
- **Pending Features**:
    - Service to set specific level (not just full refill).

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
