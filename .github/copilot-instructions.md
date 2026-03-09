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
- **`button.py`**: Triggers actions (Add Bag) on the `tracker.py`.
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
- **Bag-Based Model**: The integration tracks pellets by weight internally. "Bag Size" (default 15 kg) defines what 100% means. The internal level can exceed bag_size_g (e.g. after adding a bag on top of remaining pellets), but the sensor caps at 100%.
- **Additive Refill**: The "Add Bag" button adds bag_size_g to the current level (does not reset to full). No calibration on refill.
- **Calibration**: Only triggered via the `set_level` service with `calibrate: true`. The user reads the kg marks on the tank and provides the observed weight. EWMA applies per-level correction factors.
- **Time Remaining Prediction**: Uses an EWMA rolling average of the effective burn rate (`avg_consumption_rate` in tracker.py). When stove is active, prediction uses current rate; when off, falls back to rolling average or last-known-power rate. The sensor uses `SensorDeviceClass.DURATION` with `UnitOfTime.SECONDS` so HA formats it as a time span.
- **Midnight Handling**: `tracker.py` uses `dt_util.utcnow()` and calculates deltas, so midnight is handled naturally.
- **Persistence**: Data is saved to `.storage/pellet_tracker.storage_{entry_id}`.
- **Brand Images**: The integration ships `brand/icon.png` for native HA UI display (2026.3+). Do not submit to the brands repository.
- **Config Migration**: V1 entries (with `tank_size`) are automatically migrated to V2 (`bag_size`) via `async_migrate_entry` in `__init__.py`.

## Documentation Maintenance
- **Automatic Updates**: Every time you make changes to the code, you MUST update the following files to reflect the new state:
    - `docs/memory_bank.md`: Update Active Context and Implemented Features.
    - `docs/technical_design.md`: Update architectural changes or logic explanations.
    - `.github/copilot-instructions.md`: Update if new patterns or rules emerge.
    - `README.md`: Update features and configuration instructions.

## Custom Prompts
This repository uses VS Code Copilot Custom Prompts defined in `.github/prompts/`.
- To create a new prompt, add a `.prompt.md` file in that directory.
- The file name determines the command (e.g., `translate.prompt.md` allows you to attach the prompt).
- Documentation: https://code.visualstudio.com/docs/copilot/customization/prompt-files

