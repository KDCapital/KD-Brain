# Changelog

All notable changes to KD Brain are documented in this file. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added — M1: Foundation + prijzen
- Home Assistant custom integration scaffold (`kd_brain`) with Config Flow, Options Flow,
  diagnostics and repairs.
- `epexprijzen.nl` price data source (day-ahead, 15-minute MTU resolution, today + tomorrow).
- Configurable all-in tariff model: market price + energy tax + supplier markup + VAT, plus a
  separate feed-in price. Nothing hardcoded.
- Price sensors (current, next, daily min/max/average, full-series data sensor) and a
  "price low" binary sensor.
- `kd_brain.recalculate` service to force a price refresh.
- Full unit and integration test suite; CI with ruff, mypy, pylint, pytest, hassfest and HACS
  validation.
