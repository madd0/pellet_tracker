# GitHub Copilot Instructions for Pellet Tracker

You are an expert AI programming assistant working on a Home Assistant custom integration called "Pellet Tracker".

## Project Overview
This integration tracks the remaining level of pellets in a pellet stove. It uses a virtual sensor approach, estimating consumption based on the stove's status and power level.

## Architecture
The project follows a "Coordinator/Tracker" pattern where logic is separated from entities.
- **`tracker.py`**: The core logic engine. It handles:
    - State persistence (using `homeassistant.helpers.storage.Store`).
    - Consumption calculations (Time * Rate).
    - Event listeners (Stove Status/Power changes).
    - Timer loops (1-minute updates).
- **`sensor.py`**: A dumb presentation layer that subscribes to `tracker.py` updates.
- **`button.py`**: Triggers actions (Refill) on the `tracker.py`.
- **`config_flow.py`**: Handles setup, inspecting target entities to provide dynamic options.

## Key Files
- `custom_components/pellet_tracker/tracker.py`: **PRIMARY LOGIC**. Modify this for math/persistence.
- `custom_components/pellet_tracker/sensor.py`: Entity definitions.
- `custom_components/pellet_tracker/config_flow.py`: UI Configuration.

## Coding Standards
- **Async/Await**: All I/O and HA interactions must be async.
- **Type Hinting**: Strictly enforced.
- **Constants**: Use `const.py` for all string literals and configuration keys.
- **Error Handling**: Gracefully handle missing entities or unavailable states in `tracker.py`.

## Specific Behaviors
- **Midnight Handling**: `tracker.py` uses `dt_util.utcnow()` and calculates deltas, so midnight is handled naturally.
- **Persistence**: Data is saved to `.storage/pellet_tracker.storage_{entry_id}`.
- **EWMA**: Auto-calibration logic resides in `tracker.py` (currently TODO).

## Documentation Maintenance
- **Automatic Updates**: Every time you make changes to the code, you MUST update the following files to reflect the new state:
    - `docs/memory_bank.md`: Update Active Context and Implemented Features.
    - `docs/technical_design.md`: Update architectural changes or logic explanations.
    - `.github/copilot-instructions.md`: Update if new patterns or rules emerge.
    - `README.md`: Update features and configuration instructions.
