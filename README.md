<p align="center"><img src="images/icon.svg" width="100" height="100" alt="Pellet Tracker Icon"></p>

# Pellet Tracker for Home Assistant

A custom integration for Home Assistant to track pellet stove consumption and remaining levels.

## Features

- **Virtual Sensor**: Estimates remaining pellets based on stove status and power level.
- **Weight-Based Tracking**: Tracks pellet level internally by weight (grams). The percentage sensor displays 0-100% based on bag size, capping at 100% even when the tank holds more.
- **Time Remaining Prediction**: Estimates how long the current pellets will last, displayed as a time span (e.g., "2 days, 05:30:00"). Uses a rolling average of burn rates and adapts to power level changes.
- **Add Bag**: One-press button to add a full bag of pellets to the current level.
- **Calibration**: Uses EWMA (Exponentially Weighted Moving Average) to learn consumption rates over time, triggered via the `set_level` service.
- **Configurable**: Set bag size, initial rates, and calibration parameters.

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
    - **Bag Size**: The weight of a standard bag of pellets in kg (default: 15). This defines what 100% means on the sensor and what is added when pressing "Add Bag".
    - **Active Statuses**: Select the status values that indicate the stove is consuming pellets (e.g., "WORK", "START").
    - **Power Levels**: A comma-separated list of power levels your stove supports (e.g., "1, 2, 3, 4, 5").
    - **Maximum Consumption Rate**: The consumption rate at the highest power level in kg/h (e.g., 1.8). The integration will calculate rates for lower levels automatically.

You can change these settings later by clicking "Configure" on the integration entry in the Devices & Services page.

### Services

#### `pellet_tracker.set_level`
Manually set the current pellet weight and optionally trigger calibration.

| Parameter | Type | Required | Default | Description |
|:---|:---|:---|:---|:---|
| `weight` | float | Yes | — | The remaining weight in kg (e.g., 3.5). |
| `entry_id` | string | Yes | — | The config entry ID of the stove. |
| `calibrate` | boolean | Yes | `false` | If `true`, the system uses the correction to adjust consumption rates via EWMA. |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to contribute.

## License

[MIT License](LICENSE)
