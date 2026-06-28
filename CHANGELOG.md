# Changelog

All notable changes to KD Brain are documented in this file. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added — M2: Telemetry & state
- Telemetry layer using the entity-adapter pattern: KD Brain reads existing Home Assistant
  entities (HomeWizard P1, Growatt, Marstek, ...) instead of duplicating those integrations.
- New options step "Devices & telemetry" to map entities for grid power, solar power, household
  load and one or more home batteries (state of charge + power), with per-unit capacity.
- Push-based telemetry coordinator that refreshes whenever a source entity changes.
- Telemetry sensors (grid power, solar power, household load, battery state of charge, battery
  power), created only when the corresponding entities are configured. Household load is derived
  from the power balance when not measured directly.
- Immutable `SystemState` snapshot (prices + telemetry) and `Telemetry` model with aggregation
  helpers; telemetry is included in diagnostics.

### Added — M1: Foundation + prijzen
- Home Assistant custom integration scaffold (`kd_brain`) with Config Flow, Options Flow,
  diagnostics and repairs.
- `epexprijzen.nl` price data source (day-ahead, 15-minute MTU resolution, today + tomorrow).
- Configurable all-in tariff model: market price + energy tax + supplier markup + VAT, plus a
  separate feed-in price and monthly standing charge. Nothing hardcoded.
- Supplier presets: pick from 21 Dutch dynamic-energy suppliers to pre-fill the markup, feed-in
  cost and monthly fee automatically, with a "manual" option for full control. Energy tax and VAT
  are national values. Dataset curated from publicly listed tariffs (epexprijzen.nl).
- Price sensors (current, next, daily min/max/average, full-series data sensor) and a
  "price low" binary sensor.
- `kd_brain.recalculate` service to force a price refresh.
- Full unit and integration test suite; CI with ruff, mypy, pylint, pytest, hassfest and HACS
  validation.
