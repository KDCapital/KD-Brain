# Changelog

All notable changes to KD Brain are documented in this file. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added — M8: Custom sidebar panel
- **Custom UI panel**: KD Brain now registers its own **KD Brain** sidebar panel
  — a self-contained web component (vanilla JS, no build step, no external chart
  libraries) with five tabs: Overzicht, Prijzen, Batterij, EV & WP and
  Instellingen. It shows a live energy-flow diagram, the price curve with
  cheap/expensive shading, battery SOC and power timelines, weekly-energy bars,
  and EV/heat-pump status with reasoning. See `docs/panel.md`.
- **In-panel configuration**: a full settings tab reads and writes every option
  live through new websocket commands (`kd_brain/config/get`,
  `kd_brain/config/update`, admin only) plus a consolidated `kd_brain/snapshot`
  command; the classic options flow remains as a fallback.
- **Setup wizard**: the initial setup now also asks for your devices/sensors and
  control mode, so you can wire everything up without visiting Options first.

### Added — M7: Dashboards, reconfigure flow & Gold polish
- **Auto-generated dashboard**: new `kd_brain.generate_dashboard` response
  service builds a Lovelace dashboard (views/cards) from whichever entities
  are actually configured for an entry — no dead cards for unconfigured
  devices. See `docs/dashboard.md`.
- **Reconfigure flow**: re-run the supplier and tariff steps against an
  existing config entry (`Settings → Devices & services → Reconfigure`)
  instead of removing and re-adding the integration.
- **Entity categories**: raw market/feed-in price, the price-data curve
  sensor, active strategy, last actuation, active control and
  safety-intervened are now marked `diagnostic`, keeping the primary
  dashboard focused on actionable entities.
- Quality Scale: Gold checklist completed (reconfigure flow, entity
  categories, availability via `CoordinatorEntity`, documentation,
  optimizer benchmarks).
- New optimizer benchmark tests (`tests/test_benchmarks.py`) guarding the
  heuristic and optional MILP optimiser's runtime over a 48h/15-minute
  horizon.

### Removed
- **Auto-generated dashboard**: the `kd_brain.generate_dashboard` service and
  `docs/dashboard.md` are removed — the built-in KD Brain sidebar panel (M8) is
  now the only UI. The `kd_brain.recalculate` service remains unchanged.

### Added — M6: EV & heat pump optimization (opt-in)
- **EV smart charging** (M6a): reads an EV charger's connected/power/SOC entities, plans a charge
  current from cheap prices, solar surplus and a target SOC, and enforces IEC 61851 (0 A or at
  least the minimum, never in between) plus anti-oscillation. Writes the current to a `number`
  control entity only in active mode. New "EV smart charging" options step and a "Recommended EV
  current" sensor.
- **Heat pump optimization** (M6b): nudges the heating curve (setpoint offset) up when electricity
  is cheap and down when it is expensive, shifting demand to cheap hours while keeping the heat
  pump on its own thermostat. Safety clamps the offset to a configurable °C limit and protects the
  compressor with a write-throttle and anti short-cycle min-dwell. Writes the offset to a `number`
  control entity only in active mode. New "Heat pump optimization" options step, a "Heat pump
  power" telemetry sensor and a "Recommended heat pump offset" sensor.

### Added — M5: Peak shaving, regulation, forecast & optional MILP
- Peak shaving and backup reserve strategies (opt-in).
- NL regulation profiles (saldering 2026 / no saldering 2027 / capacity 2029) that change how
  exported energy is valued.
- AI-ready PV/weather forecasting interface with an entity-based default reading an external PV
  forecast integration (e.g. Forecast.Solar).
- Optional exact **MILP optimiser** (HiGHS via `highspy`) that solves the cost-optimal
  charge/discharge schedule over the price horizon. Selectable per entry; **`highspy` is an
  optional dependency** (not bundled). If MILP is selected but highspy is missing, KD Brain
  transparently falls back to the heuristic optimiser and raises a repair.

### Added — M4: Safety layer & actuators (opt-in control)
- Mandatory **safety gate** that every actuation passes: SOC limits (hard block), power clamp,
  anti-oscillation min-dwell, write-throttle and no-write-if-unchanged hysteresis. It can clamp to
  idle or a lower power and records human-readable reasons; it cannot be overridden by a strategy.
- **Actuator layer**: drives an existing Home Assistant `number` control entity (signed power:
  + charge / − discharge) via `number.set_value`, reusing the battery integration's own write path
  instead of writing raw Modbus/MQTT. Dry-run is the default null actuator.
- **Actuation coordinator** that runs each decision through the safety gate and, only in active
  mode, writes the approved setpoint; fires a `kd_brain_actuation` event.
- New options step "Control & safety": control mode (observe-only ↔ active, **off by default**),
  battery power control entity, write-throttle, min-dwell and hysteresis.
- New entities: "Last actuation" sensor (with safety reasons), "Active control" and
  "Safety intervened" binary sensors. Actuation included in diagnostics.
- KD Brain only steers hardware after the user explicitly switches to active mode.

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
