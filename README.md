# Pellet Tracker for Home Assistant

<img src="images/icon.svg" align="right" width="100" height="100" alt="Pellet Tracker Icon">

A custom integration for Home Assistant to track pellet stove consumption and remaining levels.

## Features

- **Virtual Sensor**: Estimates remaining pellets based on stove status and power level.
- **Calibration**: Uses EWMA (Exponentially Weighted Moving Average) to learn consumption rates over time.
- **Configurable**: Set tank size, initial rates, and calibration parameters.

## Documentation

For a detailed explanation of how the integration works, including the math behind the consumption model and the auto-calibration logic, please see the [Technical Design Document](docs/technical_design.md).

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant.
2. Go to "Integrations".
3. Click the three dots in the top right corner and select "Custom repositories".
4. Add the URL of this repository and select "Integration" as the category.
5. Click "Add".
6. Find "Pellet Tracker" in the list and install it.
7. Restart Home Assistant.

### Manual

1. Copy the `custom_components/pellet_tracker` directory to your `config/custom_components` directory.
2. Restart Home Assistant.

## Configuration

1. Go to Settings > Devices & Services.
2. Click "Add Integration".
3. Search for "Pellet Tracker".
4. Follow the configuration steps:
    - **Name**: Give your stove a friendly name (e.g., "Living Room Stove").
    - **Status Entity**: The sensor indicating if the stove is On/Off/Heating.
    - **Power Entity**: The sensor indicating the current power level (e.g., 1-5).
    - **Tank Size**: The capacity of your pellet tank in kg.
    - **Active Statuses**: Select the status values that indicate the stove is consuming pellets (e.g., "WORK", "START").
    - **Power Levels**: A comma-separated list of power levels your stove supports (e.g., "1, 2, 3, 4, 5").
    - **Maximum Consumption Rate**: The consumption rate at the highest power level in kg/h (e.g., 1.8). The integration will calculate rates for lower levels automatically.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to contribute.

## License

MIT License
