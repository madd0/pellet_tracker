# GitHub Copilot Instructions for Pellet Tracker

You are an expert AI programming assistant working on a Home Assistant custom integration called "Pellet Tracker".

## Project Overview
This integration tracks the remaining level of pellets in a pellet stove. It uses a virtual sensor approach, estimating consumption based on the stove's status and power level. It also features an auto-calibration mechanism using EWMA (Exponentially Weighted Moving Average).

## Key Components
- **`custom_components/pellet_tracker/`**: The main integration directory.
- **`sensor.py`**: Contains the `PelletTrackerSensor` class.
- **`config_flow.py`**: Handles the configuration UI.
- **`__init__.py`**: Sets up the integration.

## Coding Standards
- Follow PEP 8 style guidelines.
- Use type hinting for all function arguments and return values.
- Use `async` / `await` for all I/O operations.
- Use Home Assistant's logging mechanism (`_LOGGER`).

## Specific Instructions
- When modifying `sensor.py`, ensure the state update logic correctly handles time intervals across midnight.
- When implementing the EWMA logic, ensure the calibration factors are persisted and restored correctly.
- Keep the `manifest.json` version updated when making significant changes.
