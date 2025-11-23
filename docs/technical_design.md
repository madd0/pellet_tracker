# Technical Design & Architecture

This document outlines the technical design, logic, and architecture of the **Pellet Tracker** custom integration for Home Assistant.

## 1. Overview

The Pellet Tracker integration creates a **Virtual Sensor** that estimates the remaining fuel level in a pellet stove. Since many stoves do not have a physical level sensor, this integration proxies the level by tracking the stove's activity over time.

It relies on two primary inputs from the stove:
1.  **Status**: Is the stove running? (e.g., `WORK`, `START`, `OFF`)
2.  **Power Level**: How hard is it working? (e.g., `1` to `6`)

## 2. Consumption Model

The core logic is based on a **Consumption Rate Model**. We assume that for every power level, the stove consumes a specific amount of pellets per hour (grams/hour).

### The Formula
The remaining pellet amount is calculated by subtracting the estimated consumption from the previous total.

$$ \text{New Level} = \text{Old Level} - (\text{Time Elapsed} \times \text{Consumption Rate}) $$

Where:
*   **Time Elapsed**: The duration since the last update (in hours).
*   **Consumption Rate**: The configured burn rate for the current power level (in grams/hour).

### Default Rates (Example)
| Power Level | Rate (g/h) |
| :--- | :--- |
| 0 (Off/Wait) | 0 |
| 1 | 250 |
| 2 | 400 |
| 3 | 600 |
| 4 | 900 |
| 5 | 1300 |
| 6 | 1800 |

## 3. Auto-Calibration (EWMA)

Pellet consumption rates are not static. They vary based on:
*   **Pellet Density/Length**: Different brands burn differently.
*   **Auger Efficiency**: Sawdust buildup can change feed rates.

To address this, the integration implements an **Exponentially Weighted Moving Average (EWMA)** algorithm to "learn" the true consumption rates over time.

### How it works
1.  The system tracks how much it *thinks* it consumed since the last fill.
2.  When the user triggers a **Refill Event** (indicating the tank is full), the system compares the *estimated* consumption against the *actual* tank capacity.
3.  It calculates an error ratio and adjusts the consumption rates for the future.

$$ \text{New Rate} = \text{Old Rate} + \alpha \times (\text{Observed Rate} - \text{Old Rate}) $$

*   **$\alpha$ (Alpha)**: The learning factor (typically 0.1 - 0.3). A higher alpha makes the system adapt faster but makes it more sensitive to outliers.

## 4. Architecture

### Components
*   **`Sensor`**: The main entity (`sensor.pellet_level`) displaying the percentage.
*   **`Storage`**: Uses `hass.helpers.storage.Store` to persist the state (current level, accumulated usage, learned rates) to disk. This ensures data survives Home Assistant restarts.
*   **`Config Flow`**: UI for setting up the integration, selecting the source entities, and defining tank size.

### State Management
The integration must handle:
*   **Midnight Crossover**: Correctly calculating time intervals that span across days.
*   **Restarts**: Saving the exact timestamp and level before shutdown and restoring it immediately upon startup to prevent data loss.

## 5. Entities

| Entity | Type | Description |
| :--- | :--- | :--- |
| `sensor.pellet_level` | Sensor | The current remaining level (0-100%). |
| `sensor.pellet_remaining` | Sensor | The estimated weight remaining (kg/g). |
| `button.pellet_refill` | Button | Trigger this when filling the tank to 100%. |
