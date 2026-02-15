# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.9.0] - 2026-02-15
### Added
- New **Time Remaining** sensor (`sensor.pellet_time_remaining`) that predicts how long the current pellets will last, displayed as a time span (e.g., "2 days, 05:30:00").
- EWMA rolling average of burn rate for smoother predictions across power level changes.
- Prediction uses current burn rate when stove is active, falls back to rolling average or last known power level when off.
- Extra attributes: `burn_rate_kg_h`, `avg_burn_rate_kg_h`, `estimated_empty_at`, `last_known_power`.

## [0.8.0] - 2026-02-14
### Added
- New **Pellet Weight** sensor (`sensor.pellet_weight`) showing the remaining weight in kg, for easier dashboarding.

## [0.7.0] - 2026-02-13
### Changed
- **Bag-Based Model**: Replaced "Tank Size" with "Bag Size" (default 15 kg). The sensor now represents 0-100% of one bag, capping at 100% even when the tank holds more than one bag's worth.
- **Additive Refill**: The "Refill" button is now "Add Bag" — it adds one bag of pellets to the current level instead of resetting to 100%.
- **Weight-Based Set Level**: The `set_level` service now accepts weight in kg instead of a percentage. The `calibrate` parameter is now required (defaults to `false`).
- **Calibration Only Via Service**: Removed automatic calibration on refill. Calibration is now only triggered via `set_level` with `calibrate: true`, based on direct observation of kg marks on the tank.

### Added
- **Config Entry Migration**: V1 entries with `tank_size` are automatically migrated to V2 with `bag_size`.

## [0.6.0] - 2025-12-02
### Fixed
- Fixed calibration for power level "0" (or any level interpolating to zero). Previously, these levels could never be calibrated because their base rate was 0. Now, all levels have a minimum base rate (5% of max rate) to bootstrap calibration.

## [0.5.0] - 2025-11-27
### Added
- Spanish and French translations.

## [0.4.0] - 2025-11-27
### Changed
- Updated `pellet_tracker.set_level` service to accept a percentage (0-100) instead of kilograms for easier estimation.

## [0.3.0] - 2025-11-24
### Added
- New service `pellet_tracker.set_level` to manually set the remaining pellet level (with optional calibration).
- Enhanced debug logging for refill and calibration events (showing before/after states and effective rates).

## [0.2.4] - 2025-11-24
### Fixed
- Fixed deprecation warning for `OptionsFlowHandler` (explicitly setting `config_entry` is deprecated).

## [0.2.3] - 2025-11-24
### Fixed
- Fixed an issue where configuration updates (like adding new power levels) were ignored because old rates were being restored from storage.

## [0.2.2] - 2025-11-24
### Changed
- Maintenance release.

## [0.2.1] - 2025-11-24
### Fixed
- Release workflow configuration (allow mutable releases).

## [0.2.0] - 2025-11-24
### Added
- EWMA auto-calibration logic.
- Release automation workflow.
- Documentation updates.

## [0.1.0] - 2025-11-23
### Added
- Initial release of Pellet Tracker.
- Virtual sensor for pellet level.
- Config flow for setup.
- Device support.
