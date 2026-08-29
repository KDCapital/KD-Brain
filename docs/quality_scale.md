# Quality Scale roadmap

KD Brain targets Home Assistant **Quality Scale Gold** and, eventually, Core inclusion.
This document tracks progress against the [Integration Quality Scale](https://developers.home-assistant.io/docs/core/integration-quality-scale/).

> Note: the machine-readable `quality_scale.yaml` is a Core-only mechanism and is intentionally
> omitted from this custom component to keep `hassfest` validation clean. This document is the
> human-readable equivalent.

## Bronze — foundation (complete)

- [x] Config flow (UI setup, no YAML)
- [x] Options flow
- [x] `DataUpdateCoordinator` for polling
- [x] Unique IDs for all entities (`{entry_id}_{key}`)
- [x] Device registry entry per config entry
- [x] Entity translations (en, nl)
- [x] `async_setup_entry` / `async_unload_entry` with clean teardown
- [x] Tests for config flow, init and entities
- [x] Diagnostics with redaction
- [x] Repairs issue for an unavailable price source
- [x] `single_config_entry` enforced

## Silver — robustness (M2–M3)

- [x] Graceful degradation when a data source is temporarily unavailable
      (coordinator marks data stale and raises a repair instead of crashing)
- [ ] Reauthentication flow for token-based sources (ENTSO-E, deferred)
- [x] Parameterised, deterministic engine tests (pure `SystemState` fixtures)
- [ ] Full test coverage of every error path

## Gold — polish (M5–M7)

- [x] Reconfigure flow (re-run supplier/tariff steps against the existing entry)
- [x] Entity categories and disabled-by-default for advanced entities (raw
      market/feed-in price, price-data curve, active strategy, last actuation,
      active control and safety-intervened are `diagnostic`)
- [x] Stale-state handling and availability for every entity (all entities are
      `CoordinatorEntity` subclasses; `available` follows
      `coordinator.last_update_success`)
- [x] Comprehensive documentation and examples (README, `docs/panel.md`)
- [x] Benchmarks for the optimization engine (heuristic + optional MILP,
      48h/15-min horizon, `tests/test_benchmarks.py`)
- [ ] ~~Auto-generated dashboard (`kd_brain.generate_dashboard` service)~~ —
      removed after M8; superseded by the built-in sidebar panel
- [x] Custom sidebar panel with in-panel configuration (M8: `panel_custom` web
      component + `kd_brain/snapshot`, `kd_brain/config/get`,
      `kd_brain/config/update` websocket commands)

## Platinum — excellence (post-Gold)

- [ ] Fully async, typed, strict-mypy clean across all layers
- [ ] No blocking I/O anywhere in the event loop
