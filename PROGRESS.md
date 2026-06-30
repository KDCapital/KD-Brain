# KD Brain — Systeemvoortgang

> Centrale voortgangstracker voor het **gehele** KD Brain HEMS-systeem (alle lagen, alle
> mijlpalen). Bijwerken bij elke afgeronde stap. Architectuurdetails staan in het ontwerpplan;
> dit bestand is het overzicht op één plek.

**Legenda:** ✅ klaar · 🟡 in uitvoering · ⬜ gepland · 🔒 geblokkeerd/afhankelijk

**Laatst bijgewerkt:** 2026-06-28 · **Huidige release:** M5 (peak shaving, regelgeving, forecast, optionele MILP) · **Versie:** 0.5.0

---

## Mijlpalen (high-level)

| # | Mijlpaal | Status | Inhoud |
|---|----------|:------:|--------|
| **M1** | Foundation + prijzen | ✅ | HACS-structuur, config/options flow, coordinator, epexprijzen.nl, prijssensoren, diagnostics, repairs, CI |
| **M2** | Telemetrie & state | ✅ | entity-adapters (HomeWizard P1, Growatt, Marstek) + telemetrie-sensoren + `SystemState` + onbalansprijzen (via entity) |
| **M3** | Engine + strategieën (dry-run) | ✅ | OptimizationCoordinator, economics (degradatie/roundtrip/marge), heuristische optimizer, `Decision`/uitlegbaarheid, 3 strategieën, aanbevolen-actie sensor |
| **M4** | Safety + actuators (echte sturing) | ✅ | Safety gate (SOC/vermogen/anti-oscillatie/throttle/hysterese), entity-actuator (number.set_value), observe→active opt-in |
| **M5** | Uitbreiding | ✅ | Peak shaving + backup-reserve, NL-regelgeving (saldering 2026/2027/2029), PV-forecast (Forecaster-interface), optionele MILP (highspy, lazy + fallback) |
| **M6** | EV & warmtepomp | ⬜ | Strategieën + safety + actuators voor laden en warmtepomp |
| **M7** | Dashboards + AI-ready + Gold | ⬜ | Auto-dashboards, `Forecaster`-interfaces voor ML, Quality Scale Gold |

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
| EV Optimization | ⬜ | M6 |
| Heat Pump Optimization | ⬜ | M6 |

### 4. Safety Layer
| Regelset | Status | Mijlpaal |
|----------|:------:|:--------:|
| Batterij (SOC, vermogen, anti-oscillatie/min-dwell) | ✅ | M4 |
| I/O-bescherming (write-throttle, no-write-if-unchanged, hysterese) | ✅ | M4 |
| EV (IEC61851 6A, load/fase-balans) | ⬜ | M6 |
| Warmtepomp (min runtime/off, anti short-cycle) | ⬜ | M6 |

### 5. Actuator Layer
| Actuator | Status | Mijlpaal |
|----------|:------:|:--------:|
| Generieke entity-actuator (number.set_value) | ✅ | M4 |
| Marstek/Growatt via control-entiteit (signed power) | ✅ | M4 |
| EVSE | ⬜ | M6 |
| Warmtepomp | ⬜ | M6 |

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
| Auto-dashboards | ⬜ | M7 |
| Quality Scale | 🟡 Bronze in zicht | doorlopend |

---

## Kwaliteit & schaalbaarheid (doorlopende doelen)
- ⬜ Quality Scale: Bronze → Silver → Gold → Platinum (zie `docs/quality_scale.md`)
- 🟡 Volledige type hints / mypy strict (M1 clean; uitbreiden per mijlpaal)
- 🟡 Test-coverage hoog houden (M1: 95%)
- ⬜ Benchmark-tests voor de optimizer (M5+)
- ⬜ HACS default repository → uiteindelijk HA Core
