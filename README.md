# KD Brain

> Open-source **Home Energy Management System (HEMS)** voor Nederland, gebouwd als native
> Home Assistant-integratie. Volledig lokaal, geen cloud-afhankelijkheid voor besturing.

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

KD Brain combineert dynamische energieprijzen, je slimme meter, thuisbatterijen, zonnepanelen,
EV-laden en warmtepompen tot één slim, uitlegbaar energiebeheersysteem. Het neemt beslissingen
op basis van een echte optimalisatie-engine — geen losse `if`-statements — en je kunt voor elke
beslissing zien **waarom** die genomen is.

> ⚠️ **Status: in actieve ontwikkeling (M1 — Foundation + prijzen).**
> De huidige release levert de fundering: dynamische EPEX-prijzen (uur + kwartier) met volledige
> all-in tariefopbouw. Sturing van hardware (batterij/PV/EV/warmtepomp) volgt in latere mijlpalen
> en is **uit** by default (KD Brain start altijd in veilige *observe-only* modus).

## Functies (M1)

- 🇳🇱 **Nederlandse day-ahead EPEX-prijzen** via [epexprijzen.nl](https://epexprijzen.nl) — vandaag
  én morgen, in **15-minuten (MTU)** resolutie met optionele uur-aggregatie.
- 💶 **All-in prijsopbouw**: kale marktprijs + energiebelasting + leveranciersopslag + BTW, plus
  aparte terugleververgoeding en vaste leveringskosten. Alle componenten configureerbaar, niets hardcoded.
- 🏷️ **Leverancier-presets**: kies je energieleverancier (21 NL dynamische leveranciers) en de opslag,
  terugleverkosten en vaste kosten worden automatisch ingevuld — of vul alles handmatig in. Energiebelasting
  en BTW zijn landelijke waarden.
- 📊 Sensoren voor huidige prijs, volgende prijs, dag-minimum/-maximum/-gemiddelde en een
  data-sensor met de volledige prijscurve (klaar voor grafieken/ApexCharts).
- 🟢 Binary sensor "prijs laag nu" t.o.v. een instelbare drempel of het daggemiddelde.
- 🩺 **Diagnostics** (zonder gevoelige data), **Repairs** bij providerstoringen, volledige
  **Config Flow** en **Options Flow** — geen YAML nodig.
- 🔌 **Telemetrie via bestaande HA-entiteiten** (M2): koppel je slimme meter, zonnepanelen en
  thuisbatterijen in **Opties → Apparaten** en KD Brain leest net-, PV-, verbruik- en batterij-
  vermogen + SOC. Geen dubbele integraties; updates komen direct binnen bij elke wijziging.
- 🧠 **Uitlegbare optimalisatie-engine** (M3): 3 in/uit-schakelbare strategieën (zelfverbruik,
  dynamische prijzen, arbitrage met echt economisch model). De sensor **Aanbevolen actie** toont
  wat KD Brain zou doen én *waarom* — inclusief alle overwogen voorstellen en waarom alternatieven
  afvielen.
- 🛡️ **Veiligheidslaag + echte sturing** (M4): zet je in **Opties → Sturing & veiligheid** op
  *Actief* (standaard uit), dan stuurt KD Brain je batterij via een door jou gekozen
  `number`-besturingsentiteit. Elke schrijfactie passeert een verplichte safety-poort: SOC-grenzen,
  vermogensbegrenzing, anti-oscillatie (min-dwell), write-throttle en hysterese. Volledig uitlegbaar
  via de sensor **Laatste sturing**.

## Roadmap

| Mijlpaal | Inhoud |
| --- | --- |
| **M1** ✅ | Foundation + prijzen |
| **M2** ✅ | Telemetrie via entity-adapters (HomeWizard P1, Growatt, Marstek) + SystemState + onbalansprijzen |
| **M3** ✅ | Optimalisatie-engine + 3 strategieën + uitlegbare beslissing (observe-only) |
| **M4** ✅ | Safety layer + actuators — echte sturing van de batterij (opt-in) |
| **M5** ✅ | Peak shaving, backup-reserve, NL-regelgeving 2026/2027/2029, PV-forecast, optionele MILP |
| **M6** ✅ | EV slim laden (IEC 61851) + warmtepomp-optimalisatie (stooklijn-offset), beide opt-in |
| M7 | Dashboards, AI-ready interfaces, Quality Scale Gold |

Zie [het architectuurplan](#architectuur) en `CHANGELOG.md` voor details.

## Installatie (HACS)

1. Voeg in HACS deze repository toe als **custom repository** (categorie *Integration*):
   `https://github.com/KDCapital/KD-Brain`.
2. Installeer **KD Brain** en herstart Home Assistant.
3. Ga naar **Instellingen → Apparaten & diensten → Integratie toevoegen** en zoek **KD Brain**.
4. Doorloop de configuratie (prijsbron + tariefcomponenten). Je kunt alles later wijzigen via
   **Configureren** (Options Flow).

> Privacy: KD Brain stuurt geen telemetrie naar buiten. De enige externe netwerkverbinding is het
> ophalen van publieke prijzen bij epexprijzen.nl. Al je instellingen blijven lokaal in Home
> Assistant (`.storage`).

## Optioneel: MILP-optimizer

KD Brain heeft een optionele exacte MILP-optimizer (HiGHS) die het kostenoptimale laad/ontlaad-schema
over de hele prijshorizon berekent. Schakel hem in via **Opties → Strategieën → Optimizer-modus →
MILP**. Dit vereist het pakket `highspy` in de Home Assistant-omgeving:

```bash
pip install highspy
```

Is `highspy` niet geïnstalleerd, dan valt KD Brain automatisch terug op de (standaard) heuristische
optimizer en toont een reparatie-melding. De heuristische modus werkt out-of-the-box zonder extra's.

## Architectuur

KD Brain is opgebouwd in lagen: **Data → Energy Engine → Strategy → Safety → Actuators**, met
Config/Options Flow, coordinators, diagnostics en repairs als dwarsverbanden. Lezen gebeurt via
coordinators, beslissen in de engine, en sturen uitsluitend via de verplichte Safety→Actuator-keten.

## Bijdragen

Zie [`CONTRIBUTING.md`](CONTRIBUTING.md). Issues en pull requests zijn welkom.

## Licentie

[MIT](LICENSE) © KD Capital.

---

*Niet gelieerd aan epexprijzen.nl, Home Assistant of de genoemde hardwarefabrikanten.*
