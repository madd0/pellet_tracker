# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
