> # 🚧 Do not use this integration yet!
> **We are still working on this project and it is not ready yet.** Installing KD Brain on a
> production Home Assistant instance is **not** recommended at this stage — things will change and
> break. _Gebruik deze integratie nog niet: we zijn er nog volop mee bezig en hij is nog niet klaar._

---

# KD Brain

> Open-source **Home Energy Management System (HEMS)** voor Nederland, gebouwd als native
> Home Assistant-integratie. Volledig lokaal, geen cloud-afhankelijkheid voor besturing.

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

KD Brain combineert dynamische energieprijzen, je slimme meter, thuisbatterijen, zonnepanelen,
EV-laden en warmtepompen tot één slim, uitlegbaar energiebeheersysteem. Het neemt beslissingen
op basis van een echte optimalisatie-engine — geen losse `if`-statements — en je kunt voor elke
beslissing zien **waarom** die genomen is. Na installatie krijg je een eigen **KD Brain-paneel**
in de zijbalk waarin je alles ziet én instelt.

> ✅ **Status: functioneel compleet t/m M8 (eigen sidebar-paneel).** De volledige data → engine →
> safety → actuator-keten werkt, met een custom UI om alles te bekijken en te configureren.
> **Sturing van hardware (batterij/PV/EV/warmtepomp) staat standaard UIT**: KD Brain start altijd
> in veilige *observe-only* modus en stuurt pas na een expliciete opt-in.

## Functies

- 🇳🇱 **Nederlandse day-ahead EPEX-prijzen** via [epexprijzen.nl](https://epexprijzen.nl) — vandaag
  én morgen, in **15-minuten (MTU)** resolutie met optionele uur-aggregatie.
- 💶 **All-in prijsopbouw**: kale marktprijs + energiebelasting + leveranciersopslag + BTW, plus
  aparte terugleververgoeding en vaste leveringskosten. Alle componenten configureerbaar, niets hardcoded.
- 🏷️ **Leverancier-presets**: kies je energieleverancier (21 NL dynamische leveranciers) en de opslag,
  terugleverkosten en vaste kosten worden automatisch ingevuld — of vul alles handmatig in. Energiebelasting
  en BTW zijn landelijke waarden.
- 📊 Sensoren voor huidige prijs, volgende prijs, dag-minimum/-maximum/-gemiddelde en een
  data-sensor met de volledige prijscurve. Plus een binary sensor **"prijs laag nu"** t.o.v. een
  instelbare drempel of het daggemiddelde.
- 🔌 **Telemetrie via bestaande HA-entiteiten**: koppel je slimme meter, zonnepanelen, thuisbatterijen,
  EV-lader en warmtepomp en KD Brain leest net-, PV-, verbruik-, batterij-, EV- en warmtepomp-vermogen
  + SOC + onbalansprijs. Geen dubbele integraties; updates komen direct binnen bij elke wijziging.
- 🧠 **Uitlegbare optimalisatie-engine**: in/uit-schakelbare strategieën (zelfverbruik, dynamische
  prijzen, arbitrage met echt economisch model, peak shaving, backup-reserve). De sensor **Aanbevolen
  actie** toont wat KD Brain zou doen én *waarom* — inclusief alle overwogen voorstellen en waarom
  alternatieven afvielen. Optioneel een exacte **MILP-optimizer** (zie onder).
- 🛡️ **Veiligheidslaag + echte sturing** (opt-in): zet je in **Instellingen → Sturing & veiligheid**
  op *Actief* (standaard uit), dan stuurt KD Brain je batterij via een door jou gekozen
  `number`-besturingsentiteit. Elke schrijfactie passeert een verplichte safety-poort: SOC-grenzen,
  vermogensbegrenzing, anti-oscillatie (min-dwell), write-throttle en hysterese. Volledig uitlegbaar
  via de sensor **Laatste sturing**.
- 🚗 **EV slim laden** (opt-in): plant een laadstroom uit goedkope prijzen, zon-overschot en een
  doel-SOC, en respecteert IEC 61851 (0 A of minimaal het minimum, nooit ertussenin).
- ♨️ **Warmtepomp-optimalisatie** (opt-in): verschuift de stooklijn (setpoint-offset) naar goedkope
  uren, met anti short-cycle-bescherming.
- 🔮 **PV-forecast** via een externe forecast-integratie (bijv. Forecast.Solar) achter een AI-ready
  `Forecaster`-interface, en **NL-regelgevingsprofielen** (saldering 2026 / geen saldering 2027 /
  capaciteit 2029) die bepalen hoe teruglevering wordt gewaardeerd.
- 🖥️ **Eigen KD Brain-paneel in de zijbalk**: een compleet custom dashboard met vijf tabs
  (Overzicht · Prijzen · Batterij · EV & WP · Instellingen), een live **energie-flow**-animatie en
  grafieken voor prijs, SOC, vermogen en week-energie. Je stelt er **alles** direct in — apparaten/
  sensoren, strategieën, sturing, EV en warmtepomp. Zie [`docs/panel.md`](docs/panel.md).
- 🩺 **Diagnostics** (zonder gevoelige data), **Repairs** bij providerstoringen, volledige
  **Config Flow**, **Options Flow** en **reconfigure-flow** — geen YAML nodig.

## Roadmap

| Mijlpaal | Inhoud |
| --- | --- |
| **M1** ✅ | Foundation + prijzen |
| **M2** ✅ | Telemetrie via entity-adapters (HomeWizard P1, Growatt, Marstek) + SystemState + onbalansprijzen |
| **M3** ✅ | Optimalisatie-engine + 3 strategieën + uitlegbare beslissing (observe-only) |
| **M4** ✅ | Safety layer + actuators — echte sturing van de batterij (opt-in) |
| **M5** ✅ | Peak shaving, backup-reserve, NL-regelgeving 2026/2027/2029, PV-forecast, optionele MILP |
| **M6** ✅ | EV slim laden (IEC 61851) + warmtepomp-optimalisatie (stooklijn-offset), beide opt-in |
| **M7** ✅ | Reconfigure-flow, entity-categorieën, optimizer-benchmarks, Quality Scale Gold |
| **M8** ✅ | Eigen sidebar-paneel (5 tabs, live grafieken) + websocket-API + in-paneel-configuratie |

Zie [het architectuurplan](#architectuur) en `CHANGELOG.md` voor details.

## Installatie (HACS)

1. Voeg in HACS deze repository toe als **custom repository** (categorie *Integration*):
   `https://github.com/KDCapital/KD-Brain`.
2. Installeer **KD Brain** en herstart Home Assistant.
3. Ga naar **Instellingen → Apparaten & diensten → Integratie toevoegen** en zoek **KD Brain**.
4. Doorloop de setup-wizard: leverancier + tariefcomponenten, daarna optioneel je apparaten/sensoren
   en de besturingsmodus. Alles is later aan te passen in het **KD Brain-paneel** of via
   **Configureren** (Options Flow).
5. Na installatie verschijnt **KD Brain** in de zijbalk. Zie je het paneel niet meteen, ververs dan
   je browser of herlaad de integratie.

> Privacy: KD Brain stuurt geen telemetrie naar buiten. De enige externe netwerkverbinding is het
> ophalen van publieke prijzen bij epexprijzen.nl. Al je instellingen blijven lokaal in Home
> Assistant (`.storage`).

## Optioneel: MILP-optimizer

KD Brain heeft een optionele exacte MILP-optimizer (HiGHS) die het kostenoptimale laad/ontlaad-schema
over de hele prijshorizon berekent. Schakel hem in via **Instellingen → Strategieën → Optimizer-modus
→ MILP**. Dit vereist het pakket `highspy` in de Home Assistant-omgeving:

```bash
pip install highspy
```

Is `highspy` niet geïnstalleerd, dan valt KD Brain automatisch terug op de (standaard) heuristische
optimizer en toont een reparatie-melding. De heuristische modus werkt out-of-the-box zonder extra's.

## Architectuur

KD Brain is opgebouwd in lagen: **Data → Energy Engine → Strategy → Safety → Actuators**, met
Config/Options Flow, coordinators, diagnostics, repairs, een websocket-API en het custom paneel als
dwarsverbanden. Lezen gebeurt via coordinators, beslissen in de engine, en sturen uitsluitend via de
verplichte Safety→Actuator-keten. Het paneel is een zelfstandig web component (vanilla JS, geen
build-step) dat live data leest en configuratie schrijft via de websocket-API.

## Bijdragen

Zie [`CONTRIBUTING.md`](CONTRIBUTING.md). Issues en pull requests zijn welkom.

## Licentie

[MIT](LICENSE) © KD Capital.

---

*Niet gelieerd aan epexprijzen.nl, Home Assistant of de genoemde hardwarefabrikanten.*
