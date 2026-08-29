# KD Brain — Systeemvoortgang

> Centrale voortgangstracker voor het **gehele** KD Brain HEMS-systeem (alle lagen, alle
> mijlpalen). Bijwerken bij elke afgeronde stap. Architectuurdetails staan in het ontwerpplan;
> dit bestand is het overzicht op één plek.

**Legenda:** ✅ klaar · 🟡 in uitvoering · ⬜ gepland · 🔒 geblokkeerd/afhankelijk

**Laatst bijgewerkt:** 2026-07-04 · **Huidige release:** M8 (Custom UI paneel) · **Versie:** 0.8.0

---

## Mijlpalen (high-level)

| # | Mijlpaal | Status | Inhoud |
|---|----------|:------:|--------|
| **M1** | Foundation + prijzen | ✅ | HACS-structuur, config/options flow, coordinator, epexprijzen.nl, prijssensoren, diagnostics, repairs, CI |
| **M2** | Telemetrie & state | ✅ | entity-adapters (HomeWizard P1, Growatt, Marstek) + telemetrie-sensoren + `SystemState` + onbalansprijzen (via entity) |
| **M3** | Engine + strategieën (dry-run) | ✅ | OptimizationCoordinator, economics (degradatie/roundtrip/marge), heuristische optimizer, `Decision`/uitlegbaarheid, 3 strategieën, aanbevolen-actie sensor |
| **M4** | Safety + actuators (echte sturing) | ✅ | Safety gate (SOC/vermogen/anti-oscillatie/throttle/hysterese), entity-actuator (number.set_value), observe→active opt-in |
| **M5** | Uitbreiding | ✅ | Peak shaving + backup-reserve, NL-regelgeving (saldering 2026/2027/2029), PV-forecast (Forecaster-interface), optionele MILP (highspy, lazy + fallback) |
| **M6** | EV & warmtepomp | ✅ | EV slim laden (planner + IEC 61851-safety + actuator) en warmtepomp-optimalisatie (stooklijn-offset + anti short-cycle-safety + actuator) |
| **M7** | Reconfigure flow + AI-ready + Gold | ✅ | Reconfigure-flow, entity-categorieën, optimizer-benchmarks, Quality Scale Gold-checklist compleet (auto-dashboard-service later weer verwijderd — zie CHANGELOG) |
| **M8** | Custom UI paneel | ✅ | Eigen sidebar-paneel (vanilla-JS web component, 5 tabs), live energie-flow + prijs/SOC/vermogen/week-grafieken, websocket-API (snapshot + config get/update), setup-wizard met apparaten + sturing |

---

## M1 — Foundation + prijzen ✅ (compleet & geverifieerd)

### Geleverde componenten
- ✅ Repo-scaffolding: `manifest.json`, `hacs.json`, `pyproject.toml`, `LICENSE` (MIT), `README`, `CONTRIBUTING`, `CHANGELOG`, `.gitignore`
- ✅ CI: GitHub Actions (ruff, ruff-format, mypy, pylint, pytest) + `validate.yml` (hassfest, HACS) + Dependabot
- ✅ Integratiekern: `const.py`, `__init__.py` (typed `runtime_data`, setup/unload), `entity.py` (device + stabiele unique_ids)
- ✅ Datalaag: `data/models.py` (`PricePoint`, `PriceSeries`), `economics.py` (`TariffConfig`, all-in/teruglever/vaste kosten), `PriceSource` protocol, `EpexPrijzenSource` (geverifieerde API)
- ✅ Leverancier-presets: `data/providers.py` (21 NL leveranciers, opslag/teruglever/vaste kosten/batterijsturing), two-step config flow met automatische prefill + handmatige optie
- ✅ Coordinator: `KDBrainPriceCoordinator` (DataUpdateCoordinator, configureerbaar interval, repairs bij storing, `kd_brain_prices_updated` event)
- ✅ Config Flow + Options Flow (alle tariefcomponenten configureerbaar, single instance)
- ✅ Diagnostics (met redactie) + Repairs (prijsbron onbereikbaar)
- ✅ Entiteiten: 8 sensoren + 1 binary sensor ("prijs laag")
- ✅ Service: `kd_brain.recalculate`
- ✅ Vertalingen: EN + NL

### Kwaliteitsgates (lokaal gedraaid tegen HA 2025.1)
- ✅ ruff (lint + format) clean
- ✅ mypy `--strict` clean (15 modules)
- ✅ pylint 10.00/10
- ✅ pytest: 23 geslaagd, 95% coverage
- ✅ Geen secrets/IP/serienummers in de repo

---

## Lagen-overzicht (over alle mijlpalen)

### 1. Data Layer
| Bron | Type | Status | Mijlpaal |
|------|------|:------:|:--------:|
| epexprijzen.nl | prijzen (REST) | ✅ | M1 |
| Eigen leverancier-tarieven | tariefmodel | ✅ | M1 |
| Leverancier-presets (21 NL) | tariefdata | ✅ | M1 |
| Onbalansprijzen | prijzen (entity-adapter) | ✅ | M2 |
| ENTSO-E (fallback) | prijzen | ⬜ | M5 |
| HomeWizard P1 | telemetrie (entity-adapter) | ✅ | M2 |
| Growatt | telemetrie (entity-adapter) ✅ / sturing (MQTT) ⬜ | 🟡 | M2/M4 |
| Marstek 5kWh ×2 | telemetrie (entity-adapter) ✅ / sturing (Modbus) ⬜ | 🟡 | M2/M4 |
| PV-/weersvoorspelling | forecast (entity) | ✅ | M5 |
| EV-lader | telemetrie (entity-adapter) ✅ / sturing (number) ✅ | ✅ | M6 |
| Warmtepomp | telemetrie (entity-adapter) ✅ / sturing (number) ✅ | ✅ | M6 |

### 2. Core / Energy Engine
| Component | Status | Mijlpaal |
|-----------|:------:|:--------:|
| `SystemState` (immutable snapshot) | ✅ | M2 |
| `OptimizationCoordinator` | ✅ | M3 |
| Economisch model (degradatie/roundtrip/marge) | ✅ | M1/M3 |
| Heuristische optimizer + cost functions | ✅ | M3 |
| MILP-solver (highspy, optioneel + fallback) | ✅ | M5 |
| `Decision`/uitlegbaarheid | ✅ | M3 |
| `Forecaster` (AI-ready interface) | ✅ | M5 |

### 3. Strategy Layer (plug-ins, per stuk in/uit)
| Strategie | Status | Mijlpaal |
|-----------|:------:|:--------:|
| Self Consumption | ✅ | M3 |
| Dynamic Pricing | ✅ | M3 |
| Arbitrage | ✅ | M3 |
| Peak Shaving | ✅ | M5 |
| Backup Reserve | ✅ | M5 |
| Solar Optimization | ⬜ | M5 |
| Grid Support | ⬜ | M5 |
| EV Optimization | ✅ | M6 |
| Heat Pump Optimization | ✅ | M6 |

### 4. Safety Layer
| Regelset | Status | Mijlpaal |
|----------|:------:|:--------:|
| Batterij (SOC, vermogen, anti-oscillatie/min-dwell) | ✅ | M4 |
| I/O-bescherming (write-throttle, no-write-if-unchanged, hysterese) | ✅ | M4 |
| EV (IEC61851 6A of 0, anti-oscillatie) | ✅ | M6 |
| Warmtepomp (offset-clamp, write-throttle, anti short-cycle) | ✅ | M6 |

### 5. Actuator Layer
| Actuator | Status | Mijlpaal |
|----------|:------:|:--------:|
| Generieke entity-actuator (number.set_value) | ✅ | M4 |
| Marstek/Growatt via control-entiteit (signed power) | ✅ | M4 |
| EVSE (laadstroom via number.set_value) | ✅ | M6 |
| Warmtepomp (stooklijn-offset via number.set_value) | ✅ | M6 |

### Cross-cutting
| Onderdeel | Status | Mijlpaal |
|-----------|:------:|:--------:|
| Config/Options Flow | ✅ | M1 |
| Diagnostics | ✅ | M1 |
| Repairs | ✅ | M1 |
| Device/Entity Registry | ✅ | M1 |
| Services | 🟡 (recalculate) | M1+ |
| Events | ✅ (prices_updated) | M1 |
| NL-regelgeving profielen (2026/2027/2029) | ✅ | M5 |
| Reconfigure-flow | ✅ | M7 |
| Optimizer-benchmarks | ✅ | M7 |
| Quality Scale | ✅ Gold-checklist compleet | M7 |
| Custom sidebar-paneel (`panel_custom` + web component) | ✅ | M8 |
| Websocket-API (snapshot + config get/update) | ✅ | M8 |
| Setup-wizard met apparaten + sturing | ✅ | M8 |

---

## Kwaliteit & schaalbaarheid (doorlopende doelen)
- ✅ Quality Scale: Bronze/Silver/Gold compleet (zie `docs/quality_scale.md`); Platinum openstaand
- 🟡 Volledige type hints / mypy strict (clean over alle modules; uitbreiden per mijlpaal)
- 🟡 Test-coverage hoog houden (M1: 95%)
- ✅ Benchmark-tests voor de optimizer (`tests/test_benchmarks.py`, M7)
- ⬜ HACS default repository → uiteindelijk HA Core
