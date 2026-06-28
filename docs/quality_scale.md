# Quality Scale roadmap

KD Brain targets Home Assistant **Quality Scale Gold** and, eventually, Core inclusion.
This document tracks progress against the [Integration Quality Scale](https://developers.home-assistant.io/docs/core/integration-quality-scale/).

> Note: the machine-readable `quality_scale.yaml` is a Core-only mechanism and is intentionally
> omitted from this custom component to keep `hassfest` validation clean. This document is the
> human-readable equivalent.

## Bronze — foundation (M1, in progress)

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

- [ ] Graceful degradation when a data source is temporarily unavailable
- [ ] Reauthentication flow for token-based sources (ENTSO-E)
- [ ] Full test coverage of error paths
- [ ] Parameterised, deterministic engine tests

## Gold — polish (M5–M7)

- [ ] Reconfigure flow
- [ ] Entity categories and disabled-by-default for advanced entities
- [ ] Stale-state handling and availability for every entity
- [ ] Comprehensive documentation and examples
- [ ] Benchmarks for the optimization engine

## Platinum — excellence (post-Gold)

- [ ] Fully async, typed, strict-mypy clean across all layers
- [ ] No blocking I/O anywhere in the event loop
