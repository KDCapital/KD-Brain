# Changelog

All notable changes to KD Brain are documented in this file. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added — M3: Optimisation engine & strategies (observe-only)
- Explainable decision engine: each round produces a `Decision` recording the chosen action,
  the winning strategy, every considered proposal with its score, and the reason each
  alternative was rejected.
- Three pluggable strategies (individually toggleable): self-consumption (use PV locally),
  dynamic pricing (charge cheap / discharge expensive) and arbitrage. Arbitrage only acts when
  the look-ahead spread beats battery degradation, round-trip losses and a safety margin — a real
  economic model, not an if-statement.
- Scoring/priority optimiser that enforces battery feasibility (min/max SOC) and ranks proposals.
- `KDBrainOptimizationCoordinator` that recomputes on every price/telemetry change and fires a
  `kd_brain_decision` event.
- New sensors: "Recommended action" (enum, with the full explanation as attributes) and
  "Active strategy".
- New options step "Strategies, economics & battery limits" (strategy toggles, degradation cost,
  round-trip efficiency, safety margin, min/max SOC, max charge/discharge power).
- KD Brain stays **observe-only**: it recommends, it does not yet control hardware (that is M4).
- Decision included in diagnostics.

### Added — M2: Imbalance (onbalans) prices
- Imbalance price support via the entity-adapter pattern: point KD Brain at an existing Home
  Assistant imbalance-price sensor (€/kWh or €/MWh, auto-converted) in the Devices step. It is
  read into the telemetry snapshot/`SystemState` and exposed as an "Imbalance price" sensor.
- A native TenneT source is intentionally not bundled: the official feed now requires a developer
  API key and there is no stable free no-auth endpoint, so reusing an existing HA entity is the
  robust, no-credentials choice. (A keyed native source can be added later, like ENTSO-E.)

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
