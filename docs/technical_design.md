# Technical Design & Architecture

This document outlines the technical design, logic, and architecture of the **Pellet Tracker** custom integration for Home Assistant.

## 1. Overview

The Pellet Tracker integration creates a **Virtual Device** that estimates the remaining fuel level in a pellet stove. Since many stoves do not have a physical level sensor, this integration proxies the level by tracking the stove's activity over time.

It relies on two primary inputs from the stove:
1.  **Status**: Is the stove running? (e.g., `WORK`, `START`, `OFF`)
2.  **Power Level**: How hard is it working? (e.g., `1` to `6`)

The integration groups its entities (Sensor, Button) under a single **Device** in Home Assistant, allowing for easy management of multiple stoves.

## 2. Consumption Model

The core logic is based on a **Consumption Rate Model**. We assume that for every power level, the stove consumes a specific amount of pellets per hour (grams/hour).

### The Formula
The remaining pellet amount is calculated by subtracting the estimated consumption from the previous total.

$$ \text{New Level} = \text{Old Level} - (\text{Time Elapsed} \times \text{Consumption Rate}) $$

Where:
*   **Time Elapsed**: The duration since the last update (in hours).
*   **Consumption Rate**: The configured burn rate for the current power level (in grams/hour).

### Rate Calculation (Interpolation)
Instead of using hardcoded defaults, the integration calculates consumption rates dynamically based on the user's configuration.

1.  **Inputs**:
    *   **Power Levels**: A list of levels (e.g., `1, 2, 3, 4, 5`).
    *   **Max Rate**: The consumption at the highest level (e.g., `2.0 kg/h`).

2.  **Logic**:
    *   The **Highest Level** is assigned the **Max Rate**.
    *   The **Lowest Level** (if > 0) is assigned a calculated minimum fraction.
    *   Intermediate levels are calculated using **Linear Interpolation**.

$$ \text{Rate}_{\text{level}} = \max\left(\frac{\text{Level Value}}{\text{Max Level Value}} \times \text{Max Rate}, \text{Min Rate}\right) $$

Where **Min Rate** = 5% of Max Rate (configurable via `DEFAULT_MIN_RATE_FACTOR` in `const.py`).

*Example*:
If Max Rate is 2000 g/h and levels are 0-5:
*   Level 5: 2000 g/h
*   Level 1: (1/5) * 2000 = 400 g/h
*   Level 0: max(0, 100) = 100 g/h (minimum rate)

The **Minimum Rate** ensures that even Level 0 (or any level that would interpolate to zero) has a non-zero base rate. This allows the EWMA calibration to learn the actual consumption for these levels over time, rather than permanently assuming zero consumption.

If the levels are non-numeric (e.g., "Low", "Med", "High"), the system falls back to index-based interpolation (33%, 66%, 100%), also with the minimum rate floor applied.

## 3. Auto-Calibration (EWMA)

Pellet consumption rates are not static. They vary based on:
*   **Pellet Density/Length**: Different brands burn differently.
*   **Auger Efficiency**: Sawdust buildup can change feed rates.

To address this, the integration implements an **Exponentially Weighted Moving Average (EWMA)** algorithm to "learn" the true consumption rates over time.

### How it works
1.  The system tracks how much it *thinks* it consumed since the last fill (`total_consumed_session_g`).
2.  It also tracks the consumption **per power level** (`session_consumption_by_level`).
3.  When the user triggers a **Refill Event**, the system checks if the tank is nearly empty (Current Level < 10% of Tank Size).
4.  If calibrating, it calculates an error ratio: `Actual (Tank Size) / Estimated`.
    *   The error ratio is clamped between 0.5 and 2.0 to prevent extreme adjustments from a single anomalous session.
5.  It updates the **Correction Factor** for each power level that was used, weighted by its contribution.

$$ \text{New Factor}_i = \text{Old Factor}_i \times (1 + \alpha \times \text{Weight}_i \times (\text{Error Ratio} - 1)) $$

Where:
*   **$\text{Weight}_i$**: $\frac{\text{Consumption at Level } i}{\text{Total Estimated Consumption}}$
*   **$\alpha$ (Alpha)**: The learning factor (0.15).

This ensures that if the stove mostly ran at Power 5, the correction is primarily applied to Power 5's rate.

## 4. Architecture

### Components
*   **`Sensor`**: The main entity (`sensor.pellet_level`) displaying the percentage.
*   **`Storage`**: Uses `hass.helpers.storage.Store` to persist the state (current level, accumulated usage, learned correction factors) to disk. This ensures data survives Home Assistant restarts. Note: Base consumption rates are *not* persisted; they are recalculated from configuration on every load to ensure config changes take effect immediately.
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
