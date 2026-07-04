# Bijdragen aan KD Brain

Bedankt voor je interesse! KD Brain streeft naar Home Assistant **Quality Scale Gold** en
uiteindelijk opname in HA Core. Daarom gelden strikte kwaliteitseisen.

## Belangrijk: geen vertrouwelijke data

Deze repository is **publiek** en wordt gebruikt om de integratie te installeren. Commit **nooit**:

- API-tokens, wachtwoorden, secrets
- IP-adressen, hostnames, serienummers van jouw apparaten
- persoonlijke meetdata of exports uit jouw Home Assistant

Alle gebruiker-specifieke configuratie hoort in Home Assistant config entries (`.storage`), niet in
git. Controleer je diff vóór elke commit.

## Ontwikkelomgeving

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Kwaliteitschecks (moeten groen zijn)

```bash
ruff check .
ruff format --check .
mypy custom_components/kd_brain
pylint custom_components/kd_brain
pytest
```

CI draait daarnaast `hassfest` en HACS-validatie.

## Richtlijnen

- Volledige type hints; `mypy --strict` clean.
- Geen blocking I/O in de event loop; alle netwerk-I/O async met timeout.
- Nieuwe data-sources, strategieën, safety-rules en actuators zijn **plug-ins** achter een
  Protocol — voeg toe zonder bestaande lagen te wijzigen.
- Elke besturingsbeslissing moet **uitlegbaar** zijn (`Decision`-object).
- Schrijf unit- en integratietests bij nieuwe functionaliteit.

## Commits & PRs

- Kleine, gefocuste commits met duidelijke berichten.
- Beschrijf in de PR wát en wáárom; verwijs naar de relevante mijlpaal (M1–M8).
