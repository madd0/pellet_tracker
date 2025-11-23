# Project Memory Bank

## Active Context
- **Current Status**: Initial MVP implemented.
- **Implemented Features**:
    - Config Flow (Name, Status, Power, Tank Size).
    - Device Grouping (Entities grouped under a unique device).
    - Virtual Sensor (0-100%).
    - Refill Button.
    - Persistence (survives restarts).
- **Pending Features**:
    - EWMA Auto-Calibration (Logic exists in design, needs implementation in `tracker.py`).
    - Service to set specific level (not just full refill).

## System Patterns
- **Tracker Pattern**: `PelletTracker` class acts as a singleton-per-config-entry. It manages its own listeners and notifies entities via a callback list.
- **Device Registry**: Each entry creates a unique Device in the HA registry, allowing multiple instances to coexist cleanly.
- **Storage**: We use `Store` with a delay to avoid thrashing disk on every update, though currently it saves on every consumption tick (might need optimization).
- **Config Flow**: Uses `async_step_params` to inspect the user's chosen entity and offer dynamic choices.

## Tech Stack
- Python 3.13+
- Home Assistant Core (Async)
- Voluptuous (Schema validation)
