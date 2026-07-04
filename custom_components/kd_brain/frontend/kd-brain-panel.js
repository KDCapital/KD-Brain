/**
 * KD Brain — custom sidebar panel (vanilla web component, no build step).
 *
 * Home Assistant injects `hass`, `narrow`, `route` and `panel` as properties.
 * Live values come from the integration's own `kd_brain/snapshot` websocket
 * command; time-series charts use HA's built-in history websocket; the settings
 * tab reads/writes options through `kd_brain/config/get` and
 * `kd_brain/config/update`. All charts are hand-drawn SVG so the panel pulls in
 * no external libraries and works fully offline.
 */

const TABS = [
  ["overview", "Overzicht"],
  ["prices", "Prijzen"],
  ["battery", "Batterij"],
  ["evhp", "EV & WP"],
  ["settings", "Instellingen"],
];

const COLORS = {
  solar: "#f5c518",
  battery: "#4caf50",
  grid: "#7e8ba3",
  home: "#42a5f5",
  ev: "#26c6da",
  hp: "#ab47bc",
  charge: "#4caf50",
  discharge: "#7e57c2",
  import: "#ef5350",
  export: "#f5c518",
  cheap: "#4caf50",
  expensive: "#ef5350",
  neutral: "#7e8ba3",
};

// Settings form description: sections -> fields. Types drive the control.
const SETTINGS = [
  {
    title: "Tarief",
    fields: [
      { key: "supplier", label: "Energieleverancier", type: "supplier" },
      { key: "price_interval", label: "Weergaveresolutie", type: "enum" },
      { key: "regulation_profile", label: "Regelgevingsprofiel", type: "enum" },
      { key: "energy_tax", label: "Energiebelasting (€/kWh)", type: "num", step: 0.0001 },
      { key: "supplier_markup", label: "Leveranciersopslag (€/kWh)", type: "num", step: 0.0001 },
      { key: "feed_in_markup", label: "Terugleverkosten (€/kWh)", type: "num", step: 0.0001 },
      { key: "monthly_fee", label: "Vaste kosten (€/maand)", type: "num", step: 0.01 },
      { key: "vat", label: "BTW (fractie)", type: "num", step: 0.01 },
      { key: "price_low_threshold", label: "Drempel lage prijs (€/kWh)", type: "num", step: 0.001 },
      { key: "update_interval_minutes", label: "Update-interval (min)", type: "num", step: 5 },
    ],
  },
  {
    title: "Apparaten",
    fields: [
      { key: "grid_power_entity", label: "Netvermogen", type: "entity", domain: "sensor", dc: "power" },
      { key: "pv_power_entity", label: "Zonne-opwek", type: "entity", domain: "sensor", dc: "power" },
      { key: "load_power_entity", label: "Huishoudelijk verbruik", type: "entity", domain: "sensor", dc: "power" },
      { key: "battery_soc_entities", label: "Batterij-SOC sensor(en)", type: "entities", domain: "sensor" },
      { key: "battery_power_entities", label: "Batterij-vermogen sensor(en)", type: "entities", domain: "sensor" },
      { key: "battery_capacity_wh", label: "Batterijcapaciteit per stuk (Wh)", type: "num", step: 100 },
      { key: "pv_forecast_power_entity", label: "PV-voorspelling vermogen", type: "entity", domain: "sensor" },
      { key: "pv_forecast_today_entity", label: "PV-voorspelling vandaag", type: "entity", domain: "sensor" },
      { key: "heatpump_power_entity", label: "Warmtepomp-vermogen", type: "entity", domain: "sensor", dc: "power" },
      { key: "imbalance_price_entity", label: "Onbalansprijs", type: "entity", domain: "sensor" },
      { key: "imbalance_unit", label: "Eenheid onbalansprijs", type: "enum" },
    ],
  },
  {
    title: "Strategieën & economie",
    fields: [
      { key: "optimizer_mode", label: "Optimizer-modus", type: "enum" },
      { key: "enable_self_consumption", label: "Zelfverbruik", type: "bool" },
      { key: "enable_dynamic_pricing", label: "Dynamische prijzen", type: "bool" },
      { key: "enable_arbitrage", label: "Arbitrage", type: "bool" },
      { key: "enable_peak_shaving", label: "Peak shaving", type: "bool" },
      { key: "enable_backup_reserve", label: "Backup-reserve", type: "bool" },
      { key: "peak_shave_import_w", label: "Peak shave import (W)", type: "num", step: 100 },
      { key: "peak_shave_export_w", label: "Peak shave export (W)", type: "num", step: 100 },
      { key: "backup_reserve_soc", label: "Backup-reserve SOC (%)", type: "num", step: 1 },
      { key: "degradation_cost", label: "Degradatiekosten (€/kWh)", type: "num", step: 0.001 },
      { key: "roundtrip_efficiency", label: "Roundtrip-rendement", type: "num", step: 0.01 },
      { key: "safety_margin", label: "Veiligheidsmarge (€/kWh)", type: "num", step: 0.001 },
      { key: "battery_min_soc", label: "Min SOC (%)", type: "num", step: 1 },
      { key: "battery_max_soc", label: "Max SOC (%)", type: "num", step: 1 },
      { key: "max_charge_power_w", label: "Max laadvermogen (W)", type: "num", step: 100 },
      { key: "max_discharge_power_w", label: "Max ontlaadvermogen (W)", type: "num", step: 100 },
    ],
  },
  {
    title: "Sturing & veiligheid",
    fields: [
      { key: "control_mode", label: "Besturingsmodus", type: "enum" },
      { key: "battery_power_control_entity", label: "Batterij-besturingsentiteit", type: "entity", domain: "number" },
      { key: "write_throttle_seconds", label: "Min. tijd tussen schrijfacties (s)", type: "num", step: 5 },
      { key: "min_dwell_seconds", label: "Min. wachttijd richtingomkering (s)", type: "num", step: 5 },
      { key: "hysteresis_w", label: "Hysterese (W)", type: "num", step: 10 },
    ],
  },
  {
    title: "EV",
    fields: [
      { key: "enable_ev", label: "EV slim laden", type: "bool" },
      { key: "ev_current_control_entity", label: "EV-stroom besturingsentiteit", type: "entity", domain: "number" },
      { key: "ev_min_current_a", label: "Min. laadstroom (A)", type: "num", step: 1 },
      { key: "ev_max_current_a", label: "Max. laadstroom (A)", type: "num", step: 1 },
      { key: "ev_phases", label: "Aantal fasen", type: "num", step: 1 },
      { key: "ev_target_soc", label: "Doel-SOC (%)", type: "num", step: 1 },
    ],
  },
  {
    title: "Warmtepomp",
    fields: [
      { key: "enable_heatpump", label: "Warmtepomp-optimalisatie", type: "bool" },
      { key: "heatpump_offset_control_entity", label: "Offset besturingsentiteit", type: "entity", domain: "number" },
      { key: "heatpump_max_offset", label: "Max. offset (°C)", type: "num", step: 0.5 },
    ],
  },
];

const fmtW = (w) => {
  if (w === null || w === undefined || Number.isNaN(w)) return "–";
  const a = Math.abs(w);
  return a >= 1000 ? `${(w / 1000).toFixed(2)} kW` : `${Math.round(w)} W`;
};
const fmtKwh = (v) => (v === null || v === undefined ? "–" : `${v.toFixed(2)} kWh`);
const fmtEur = (v) => (v === null || v === undefined ? "–" : `€ ${Number(v).toFixed(3)}`);
const fmtPct = (v) => (v === null || v === undefined ? "–" : `${Math.round(v)} %`);

class KdBrainPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._tab = "overview";
    this._snapshot = null;
    this._config = null;
    this._built = false;
    this._historyCache = {};
    this._poll = null;
    this._toast = "";
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._built) {
      this._build();
      this._built = true;
      this._loadConfig();
      this._refreshSnapshot();
      this._poll = setInterval(() => this._refreshSnapshot(), 5000);
    }
  }

  set panel(_p) {}
  set narrow(_n) {}
  set route(_r) {}

  disconnectedCallback() {
    if (this._poll) clearInterval(this._poll);
  }

  async _loadConfig() {
    try {
      this._config = await this._hass.callWS({ type: "kd_brain/config/get" });
      this._render();
    } catch (e) {
      /* not admin or not loaded yet */
    }
  }

  async _refreshSnapshot() {
    try {
      this._snapshot = await this._hass.callWS({ type: "kd_brain/snapshot" });
      if (this._tab !== "settings") this._render();
    } catch (e) {
      /* entry reloading */
    }
  }

  _setTab(tab) {
    this._tab = tab;
    this._render();
    if (tab === "overview") this._loadWeekly();
    if (tab === "battery") this._loadBatteryHistory();
  }

  // ---- data helpers -------------------------------------------------------

  _opt(key, fallback) {
    const o = (this._config && this._config.options) || {};
    return o[key] === undefined ? fallback : o[key];
  }

  async _fetchHistory(entityIds, start, end) {
    const ids = entityIds.filter(Boolean);
    if (!ids.length) return {};
    try {
      const res = await this._hass.callWS({
        type: "history/history_during_period",
        start_time: start.toISOString(),
        end_time: end.toISOString(),
        entity_ids: ids,
        minimal_response: false,
        no_attributes: true,
        significant_changes_only: false,
      });
      const out = {};
      for (const id of ids) {
        const rows = res[id] || [];
        out[id] = rows
          .map((r) => {
            const v = parseFloat(r.s !== undefined ? r.s : r.state);
            const t = r.lu !== undefined ? new Date(r.lu * 1000) : new Date(r.last_changed);
            return { t, v };
          })
          .filter((p) => !Number.isNaN(p.v));
      }
      return out;
    } catch (e) {
      return {};
    }
  }

  async _loadBatteryHistory() {
    const end = new Date();
    const start = new Date(end.getTime() - 24 * 3600 * 1000);
    const soc = [].concat(this._opt("battery_soc_entities", []) || []);
    const power = [].concat(this._opt("battery_power_entities", []) || []);
    const pv = this._opt("pv_power_entity");
    const grid = this._opt("grid_power_entity");
    const ids = [...soc, ...power, pv, grid];
    this._historyCache.battery = await this._fetchHistory(ids, start, end);
    if (this._tab === "battery") this._render();
  }

  async _loadWeekly() {
    if (this._historyCache.weekly) return;
    const end = new Date();
    const start = new Date(end.getTime() - 7 * 24 * 3600 * 1000);
    const grid = this._opt("grid_power_entity");
    const power = [].concat(this._opt("battery_power_entities", []) || []);
    const ids = [grid, ...power];
    const hist = await this._fetchHistory(ids, start, end);
    this._historyCache.weekly = this._buildWeekly(hist, grid, power);
    if (this._tab === "overview") this._render();
  }

  // Integrate signed power (W) series into daily kWh buckets (approximation).
  _buildWeekly(hist, grid, powerIds) {
    const days = {};
    const key = (d) => d.toLocaleDateString("nl-NL", { weekday: "short" });
    const addSeries = (series, posField, negField) => {
      if (!series || series.length < 2) return;
      for (let i = 1; i < series.length; i++) {
        const dtH = (series[i].t - series[i - 1].t) / 3600000;
        if (dtH <= 0 || dtH > 2) continue;
        const w = series[i - 1].v;
        const kwh = (Math.abs(w) * dtH) / 1000;
        const k = key(series[i - 1].t);
        days[k] = days[k] || { charge: 0, discharge: 0, import: 0, export: 0 };
        if (w >= 0) days[k][posField] += kwh;
        else days[k][negField] += kwh;
      }
    };
    if (grid) addSeries(hist[grid], "import", "export");
    // sum battery power series pointwise is hard across timestamps; integrate each
    for (const id of powerIds) addSeries(hist[id], "charge", "discharge");
    return days;
  }

  _entityOptions(domain, dc) {
    const states = this._hass.states || {};
    const out = [];
    for (const id of Object.keys(states)) {
      if (domain && !id.startsWith(domain + ".")) continue;
      if (dc) {
        const cls = states[id].attributes.device_class;
        const unit = (states[id].attributes.unit_of_measurement || "").toLowerCase();
        if (cls !== dc && !(dc === "power" && ["w", "kw", "mw"].includes(unit))) continue;
      }
      out.push(id);
    }
    return out.sort();
  }

  // ---- rendering ----------------------------------------------------------

  _build() {
    this.shadowRoot.innerHTML = `
      <style>
        :host { display:block; color:var(--primary-text-color,#e1e1e1);
          font-family:var(--paper-font-body1_-_font-family,Roboto,sans-serif); }
        .wrap { max-width:1500px; margin:0 auto; padding:16px; }
        header.bar { display:flex; align-items:center; gap:16px; margin-bottom:16px; flex-wrap:wrap; }
        .logo { font-size:20px; font-weight:600; letter-spacing:.3px; }
        .logo small { display:block; font-size:11px; opacity:.6; font-weight:400; }
        nav { display:flex; gap:6px; flex-wrap:wrap; }
        nav button { background:var(--card-background-color,#1c1c1c); color:inherit;
          border:1px solid var(--divider-color,#333); border-radius:20px; padding:7px 16px;
          cursor:pointer; font-size:13px; }
        nav button.active { background:var(--primary-color,#03a9f4); color:#fff; border-color:transparent; }
        .grid { display:grid; gap:16px; grid-template-columns:repeat(auto-fit,minmax(320px,1fr)); }
        .card { background:var(--card-background-color,#1c1c1c); border-radius:14px; padding:18px;
          box-shadow:var(--ha-card-box-shadow,0 2px 6px rgba(0,0,0,.3)); }
        .card h2 { margin:0 0 14px; font-size:13px; text-transform:uppercase; letter-spacing:.6px; opacity:.65; }
        .rows { display:flex; flex-direction:column; gap:9px; }
        .row { display:flex; justify-content:space-between; align-items:center; font-size:14px; }
        .row .k { opacity:.7; }
        .row .v { font-weight:600; }
        .pill { padding:2px 10px; border-radius:12px; font-size:12px; font-weight:600; }
        .pill.green { background:rgba(76,175,80,.22); color:#7bd88f; }
        .pill.grey { background:rgba(126,139,163,.22); color:#aab4c5; }
        .pill.blue { background:rgba(66,165,245,.22); color:#7cc0f5; }
        .big { font-size:30px; font-weight:700; }
        .muted { opacity:.6; font-size:12px; }
        label.f { display:flex; flex-direction:column; gap:4px; font-size:12px; opacity:.85; margin-bottom:10px; }
        label.f input, label.f select { background:var(--secondary-background-color,#111);
          color:inherit; border:1px solid var(--divider-color,#333); border-radius:8px; padding:8px; font-size:13px; }
        .save { background:var(--primary-color,#03a9f4); color:#fff; border:none; border-radius:10px;
          padding:11px 22px; font-size:14px; cursor:pointer; margin-top:6px; }
        .toast { position:fixed; bottom:24px; left:50%; transform:translateX(-50%);
          background:var(--primary-color,#03a9f4); color:#fff; padding:10px 20px; border-radius:10px;
          font-size:13px; opacity:0; transition:opacity .3s; pointer-events:none; }
        .toast.show { opacity:1; }
        svg { width:100%; height:auto; display:block; }
        .chip { display:inline-block; padding:2px 8px; border-radius:8px; font-size:11px;
          background:var(--secondary-background-color,#111); margin:2px 4px 2px 0; }
        ul.reasons { margin:6px 0 0; padding-left:18px; font-size:12px; opacity:.8; }
      </style>
      <div class="wrap">
        <header class="bar">
          <div class="logo">KD Brain<small>Energy Manager</small></div>
          <nav id="nav"></nav>
        </header>
        <div id="view"></div>
      </div>
      <div class="toast" id="toast"></div>
    `;
    const nav = this.shadowRoot.getElementById("nav");
    for (const [id, label] of TABS) {
      const b = document.createElement("button");
      b.textContent = label;
      b.dataset.tab = id;
      b.addEventListener("click", () => this._setTab(id));
      nav.appendChild(b);
    }
    this._render();
  }

  _render() {
    if (!this._built) return;
    for (const b of this.shadowRoot.querySelectorAll("nav button")) {
      b.classList.toggle("active", b.dataset.tab === this._tab);
    }
    const view = this.shadowRoot.getElementById("view");
    if (!view) return;
    let html = "";
    if (this._tab === "overview") html = this._viewOverview();
    else if (this._tab === "prices") html = this._viewPrices();
    else if (this._tab === "battery") html = this._viewBattery();
    else if (this._tab === "evhp") html = this._viewEvHp();
    else if (this._tab === "settings") html = this._viewSettings();
    view.innerHTML = html;
    if (this._tab === "settings") this._wireSettings();
  }

  _toastMsg(text) {
    const el = this.shadowRoot.getElementById("toast");
    if (!el) return;
    el.textContent = text;
    el.classList.add("show");
    setTimeout(() => el.classList.remove("show"), 2500);
  }

  // ---- Overview -----------------------------------------------------------

  _viewOverview() {
    const s = this._snapshot;
    if (!s) return `<div class="card">Laden…</div>`;
    const t = s.telemetry || {};
    const dec = s.decision;
    const soc = t.battery_soc_average;
    const active = s.active_control;
    const status = `
      <div class="card">
        <h2>Systeemstatus</h2>
        <div class="rows">
          <div class="row"><span class="k">Modus</span>
            <span class="pill ${active ? "green" : "grey"}">${active ? "Actief" : "Observatie"}</span></div>
          <div class="row"><span class="k">Aanbevolen actie</span>
            <span class="v">${dec ? dec.action : "–"}</span></div>
          <div class="row"><span class="k">Actieve strategie</span>
            <span class="v">${dec ? dec.strategy : "–"}</span></div>
          <div class="row"><span class="k">Batterij-SOC</span><span class="v">${fmtPct(soc)}</span></div>
          <div class="row"><span class="k">Batterij-vermogen</span><span class="v">${fmtW(t.battery_power_total_w)}</span></div>
        </div>
        ${dec ? `<div class="muted" style="margin-top:12px">${dec.why || ""}</div>` : ""}
      </div>`;

    const flow = `<div class="card"><h2>Energie-flow</h2>${this._energyFlow(s)}</div>`;

    const p = s.prices || {};
    const today = `
      <div class="card">
        <h2>Vandaag</h2>
        <div class="rows">
          <div class="row"><span class="k">Huidige prijs</span><span class="v">${fmtEur(p.current_all_in)}</span></div>
          <div class="row"><span class="k">Gemiddeld</span><span class="v">${fmtEur(p.average_all_in)}</span></div>
          <div class="row"><span class="k">Min / Max</span><span class="v">${fmtEur(p.min_all_in)} / ${fmtEur(p.max_all_in)}</span></div>
          <div class="row"><span class="k">PV-voorspelling vandaag</span><span class="v">${fmtKwh(s.forecast && s.forecast.pv_energy_today_kwh)}</span></div>
        </div>
      </div>`;

    const weekly = `<div class="card"><h2>Week-energie (benadering)</h2>${this._weeklyBars()}</div>`;

    return `<div class="grid">${status}${flow}${today}${weekly}</div>`;
  }

  _energyFlow(s) {
    const t = s.telemetry || {};
    const grid = t.grid_power_w;
    const pv = t.pv_power_w;
    const batt = t.battery_power_total_w;
    const load = t.load_power_w;
    const ev = (t.ev && t.ev.charging_power_w) || null;
    const hp = (t.heat_pump && t.heat_pump.power_w) || null;
    const thr = 20;
    const node = (x, y, color, label, val) => `
      <circle cx="${x}" cy="${y}" r="30" fill="${color}22" stroke="${color}" stroke-width="2"/>
      <text x="${x}" y="${y - 2}" text-anchor="middle" font-size="10" fill="var(--primary-text-color,#eee)">${label}</text>
      <text x="${x}" y="${y + 12}" text-anchor="middle" font-size="10" font-weight="700" fill="var(--primary-text-color,#eee)">${val}</text>`;
    // link from a->b; dir>0 draws animation a->b, dir<0 b->a, 0 idle
    const link = (x1, y1, x2, y2, color, active, reverse) => {
      const cls = active ? "flow" : "";
      const off = reverse ? "" : `<animate attributeName="stroke-dashoffset" from="0" to="-16" dur="0.7s" repeatCount="indefinite"/>`;
      const offR = reverse ? `<animate attributeName="stroke-dashoffset" from="-16" to="0" dur="0.7s" repeatCount="indefinite"/>` : "";
      return `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${color}"
        stroke-width="${active ? 3 : 1.5}" stroke-dasharray="${active ? "6 6" : "2 6"}" opacity="${active ? 0.95 : 0.35}">
        ${active ? off + offR : ""}</line>`;
    };
    const cx = 250, cy = 150;
    const solar = [250, 40], gridN = [70, 150], battery = [250, 260], evN = [430, 90], hpN = [430, 210];
    return `
      <svg viewBox="0 0 500 300" role="img" aria-label="Energie-flow">
        ${link(solar[0], solar[1], cx, cy, COLORS.solar, pv !== null && pv > thr, false)}
        ${link(gridN[0], gridN[1], cx, cy, COLORS.grid, grid !== null && Math.abs(grid) > thr, grid < 0)}
        ${link(battery[0], battery[1], cx, cy, COLORS.battery, batt !== null && Math.abs(batt) > thr, batt > 0)}
        ${link(cx, cy, evN[0], evN[1], COLORS.ev, ev !== null && ev > thr, false)}
        ${link(cx, cy, hpN[0], hpN[1], COLORS.hp, hp !== null && hp > thr, false)}
        ${node(cx, cy, COLORS.home, "Huis", fmtW(load))}
        ${node(solar[0], solar[1], COLORS.solar, "Zon", fmtW(pv))}
        ${node(gridN[0], gridN[1], COLORS.grid, "Net", fmtW(grid))}
        ${node(battery[0], battery[1], COLORS.battery, "Accu", fmtW(batt))}
        ${node(evN[0], evN[1], COLORS.ev, "EV", fmtW(ev))}
        ${node(hpN[0], hpN[1], COLORS.hp, "WP", fmtW(hp))}
      </svg>`;
  }

  _weeklyBars() {
    const w = this._historyCache.weekly;
    if (!w) {
      this._loadWeekly();
      return `<div class="muted">Laden…</div>`;
    }
    const keys = Object.keys(w);
    if (!keys.length) return `<div class="muted">Geen historische data (koppel netvermogen/batterij-sensoren).</div>`;
    const groups = keys.map((d) => ({ label: d, ...w[d] }));
    return this._svgBars(groups, ["charge", "discharge", "import", "export"],
      [COLORS.charge, COLORS.discharge, COLORS.import, COLORS.export],
      ["Laden", "Ontladen", "Import", "Export"]);
  }

  // ---- Prices -------------------------------------------------------------

  _viewPrices() {
    const s = this._snapshot;
    if (!s || !s.prices || !s.prices.available) return `<div class="card">Geen prijsdata.</div>`;
    const p = s.prices;
    const stats = `
      <div class="card">
        <h2>Prijzen vandaag</h2>
        <div class="rows">
          <div class="row"><span class="k">Nu (all-in)</span><span class="v">${fmtEur(p.current_all_in)}</span></div>
          <div class="row"><span class="k">Gemiddeld</span><span class="v">${fmtEur(p.average_all_in)}</span></div>
          <div class="row"><span class="k">Minimum</span><span class="v">${fmtEur(p.min_all_in)}</span></div>
          <div class="row"><span class="k">Maximum</span><span class="v">${fmtEur(p.max_all_in)}</span></div>
          <div class="row"><span class="k">Drempel goedkoop</span><span class="v">${fmtEur(p.threshold)}</span></div>
        </div>
      </div>`;
    const todayCard = `<div class="card"><h2>Curve vandaag</h2>${this._priceCurve(p.today, p)}</div>`;
    const tmrCard = p.tomorrow && p.tomorrow.length
      ? `<div class="card"><h2>Curve morgen</h2>${this._priceCurve(p.tomorrow, p)}</div>`
      : "";
    return `<div class="grid">${stats}${todayCard}${tmrCard}</div>`;
  }

  _priceCurve(points, p) {
    if (!points || !points.length) return `<div class="muted">Geen data.</div>`;
    const w = 500, h = 220, pad = 30;
    const vals = points.map((x) => x.all_in);
    const min = Math.min(...vals, 0);
    const max = Math.max(...vals, p.threshold || 0);
    const span = max - min || 1;
    const bw = (w - 2 * pad) / points.length;
    const now = new Date();
    let bars = "";
    points.forEach((pt, i) => {
      const v = pt.all_in;
      const bh = ((v - min) / span) * (h - 2 * pad);
      const x = pad + i * bw;
      const y = h - pad - bh;
      let color = COLORS.neutral;
      if (v <= p.threshold) color = COLORS.cheap;
      else if (p.average_all_in && v >= p.average_all_in) color = COLORS.expensive;
      const current = new Date(pt.start) <= now && now < new Date(pt.end);
      bars += `<rect x="${x + 0.5}" y="${y}" width="${Math.max(bw - 1, 1)}" height="${bh}"
        fill="${color}" opacity="${current ? 1 : 0.65}"${current ? ' stroke="#fff" stroke-width="1"' : ""}/>`;
    });
    // average line
    let avgLine = "";
    if (p.average_all_in) {
      const y = h - pad - ((p.average_all_in - min) / span) * (h - 2 * pad);
      avgLine = `<line x1="${pad}" y1="${y}" x2="${w - pad}" y2="${y}" stroke="#fff" stroke-dasharray="4 4" opacity=".5"/>
        <text x="${w - pad}" y="${y - 4}" text-anchor="end" font-size="10" fill="#fff" opacity=".6">gem</text>`;
    }
    const axis = `<text x="${pad}" y="14" font-size="10" fill="#fff" opacity=".6">${fmtEur(max)}</text>
      <text x="${pad}" y="${h - pad + 14}" font-size="10" fill="#fff" opacity=".6">${points[0].start.slice(11, 16)}</text>
      <text x="${w - pad}" y="${h - pad + 14}" text-anchor="end" font-size="10" fill="#fff" opacity=".6">${points[points.length - 1].start.slice(11, 16)}</text>`;
    return `<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Prijscurve">${bars}${avgLine}${axis}</svg>`;
  }

  // ---- Battery ------------------------------------------------------------

  _viewBattery() {
    const s = this._snapshot;
    if (!s) return `<div class="card">Laden…</div>`;
    const t = s.telemetry || {};
    const hist = this._historyCache.battery;
    if (!hist) this._loadBatteryHistory();

    const socId = ([].concat(this._opt("battery_soc_entities", []) || []))[0];
    const socSeries = hist && socId ? hist[socId] : null;
    const socCard = `<div class="card"><h2>SOC vandaag</h2>${
      socSeries ? this._svgLine([{ color: COLORS.battery, points: socSeries }], { yMin: 0, yMax: 100, unit: "%" })
        : `<div class="big">${fmtPct(t.battery_soc_average)}</div><div class="muted">Geen SOC-historie geconfigureerd.</div>`
    }</div>`;

    const powIds = [].concat(this._opt("battery_power_entities", []) || []);
    const pv = this._opt("pv_power_entity");
    const grid = this._opt("grid_power_entity");
    const series = [];
    if (hist) {
      if (hist[grid]) series.push({ color: COLORS.grid, points: hist[grid], label: "Net" });
      if (hist[pv]) series.push({ color: COLORS.solar, points: hist[pv], label: "Zon" });
      if (powIds[0] && hist[powIds[0]]) series.push({ color: COLORS.battery, points: hist[powIds[0]], label: "Accu" });
    }
    const powerCard = `<div class="card"><h2>Vermogen (24u)</h2>${
      series.length ? this._svgLine(series, { unit: "W" }) + this._legend(series)
        : `<div class="muted">Geen vermogen-historie geconfigureerd.</div>`
    }</div>`;

    const perBatt = (t.batteries || []).map((b, i) => `
      <div class="row"><span class="k">Accu ${i + 1}</span>
        <span class="v">${fmtPct(b.soc)} · ${fmtW(b.power_w)}${b.temp_c != null ? " · " + b.temp_c + "°C" : ""}</span></div>`).join("");
    const detail = `<div class="card"><h2>Batterijen</h2><div class="rows">
      <div class="row"><span class="k">Gem. SOC</span><span class="v">${fmtPct(t.battery_soc_average)}</span></div>
      <div class="row"><span class="k">Totaal vermogen</span><span class="v">${fmtW(t.battery_power_total_w)}</span></div>
      <div class="row"><span class="k">Capaciteit</span><span class="v">${t.battery_capacity_total_wh ? (t.battery_capacity_total_wh / 1000).toFixed(1) + " kWh" : "–"}</span></div>
      ${perBatt}
      <div class="row"><span class="k">Min / Max SOC</span><span class="v">${this._opt("battery_min_soc", "–")}% / ${this._opt("battery_max_soc", "–")}%</span></div>
    </div></div>`;

    return `<div class="grid">${detail}${socCard}${powerCard}</div>`;
  }

  // ---- EV & Heat pump -----------------------------------------------------

  _viewEvHp() {
    const s = this._snapshot;
    if (!s) return `<div class="card">Laden…</div>`;
    const ev = s.ev;
    const hp = s.heatpump;
    const evEnabled = !!this._opt("enable_ev", false);
    const hpEnabled = !!this._opt("enable_heatpump", false);

    const evReasons = ev && ev.reasons ? `<ul class="reasons">${ev.reasons.map((r) => `<li>${r}</li>`).join("")}</ul>` : "";
    const evCard = `<div class="card"><h2>EV slim laden</h2>
      <div class="rows">
        <div class="row"><span class="k">Ingeschakeld</span><span class="pill ${evEnabled ? "green" : "grey"}">${evEnabled ? "Ja" : "Nee"}</span></div>
        <div class="row"><span class="k">Verbonden</span><span class="v">${ev && ev.connected != null ? (ev.connected ? "Ja" : "Nee") : "–"}</span></div>
        <div class="row"><span class="k">Aanbevolen stroom</span><span class="v">${ev ? ev.current_a + " A" : "–"}</span></div>
        <div class="row"><span class="k">Doel-SOC</span><span class="v">${this._opt("ev_target_soc", "–")}%</span></div>
        <div class="row"><span class="k">Geschreven</span><span class="v">${ev ? (ev.written ? "Ja" : "Nee") : "–"}</span></div>
      </div>${evReasons}</div>`;

    const hpReasons = hp && hp.reasons ? `<ul class="reasons">${hp.reasons.map((r) => `<li>${r}</li>`).join("")}</ul>` : "";
    const hpCard = `<div class="card"><h2>Warmtepomp</h2>
      <div class="rows">
        <div class="row"><span class="k">Ingeschakeld</span><span class="pill ${hpEnabled ? "green" : "grey"}">${hpEnabled ? "Ja" : "Nee"}</span></div>
        <div class="row"><span class="k">Vermogen</span><span class="v">${fmtW(hp && hp.power_w)}</span></div>
        <div class="row"><span class="k">Aanbevolen offset</span><span class="v">${hp ? hp.offset_c.toFixed(1) + " °C" : "–"}</span></div>
        <div class="row"><span class="k">Max offset</span><span class="v">${this._opt("heatpump_max_offset", "–")} °C</span></div>
        <div class="row"><span class="k">Geschreven</span><span class="v">${hp ? (hp.written ? "Ja" : "Nee") : "–"}</span></div>
      </div>${hpReasons}</div>`;

    return `<div class="grid">${evCard}${hpCard}</div>`;
  }

  // ---- Settings -----------------------------------------------------------

  _viewSettings() {
    if (!this._config) return `<div class="card">Instellingen laden…</div>`;
    const enums = this._config.enums || {};
    const providers = this._config.providers || [];
    let sections = "";
    for (const sec of SETTINGS) {
      let fields = "";
      for (const f of sec.fields) {
        const val = this._opt(f.key, "");
        fields += this._settingsField(f, val, enums, providers);
      }
      sections += `<div class="card"><h2>${sec.title}</h2>${fields}</div>`;
    }
    return `<div class="grid">${sections}</div>
      <div style="margin-top:16px"><button class="save" id="save">Instellingen opslaan</button>
      <span class="muted" style="margin-left:12px">Wijzigingen herladen de integratie.</span></div>`;
  }

  _settingsField(f, val, enums, providers) {
    const id = `f_${f.key}`;
    if (f.type === "bool") {
      return `<label class="f" style="flex-direction:row;justify-content:space-between;align-items:center">
        <span>${f.label}</span>
        <input type="checkbox" id="${id}" data-key="${f.key}" data-type="bool" ${val ? "checked" : ""}/></label>`;
    }
    if (f.type === "num") {
      return `<label class="f">${f.label}
        <input type="number" id="${id}" data-key="${f.key}" data-type="num" step="${f.step || "any"}" value="${val === "" || val == null ? "" : val}"/></label>`;
    }
    if (f.type === "enum") {
      const opts = (enums[f.key] || []).map((o) => `<option value="${o}" ${o === val ? "selected" : ""}>${o}</option>`).join("");
      return `<label class="f">${f.label}<select id="${id}" data-key="${f.key}" data-type="str">${opts}</select></label>`;
    }
    if (f.type === "supplier") {
      const opts = providers.map((p) => `<option value="${p.id}" ${p.id === val ? "selected" : ""}>${p.name}</option>`).join("");
      return `<label class="f">${f.label}<select id="${id}" data-key="${f.key}" data-type="str">${opts}</select></label>`;
    }
    if (f.type === "entity" || f.type === "entities") {
      const multi = f.type === "entities";
      const cur = multi ? [].concat(val || []) : [val];
      const options = this._entityOptions(f.domain, f.dc);
      const optHtml = [`<option value="">— geen —</option>`]
        .concat(options.map((e) => `<option value="${e}" ${cur.includes(e) ? "selected" : ""}>${e}</option>`))
        .join("");
      return `<label class="f">${f.label}
        <select id="${id}" data-key="${f.key}" data-type="${multi ? "entities" : "entity"}" ${multi ? "multiple size=4" : ""}>${optHtml}</select></label>`;
    }
    return "";
  }

  _wireSettings() {
    const btn = this.shadowRoot.getElementById("save");
    if (!btn) return;
    btn.addEventListener("click", async () => {
      const changes = {};
      for (const el of this.shadowRoot.querySelectorAll("[data-key]")) {
        const key = el.dataset.key;
        const type = el.dataset.type;
        if (type === "bool") changes[key] = el.checked;
        else if (type === "num") changes[key] = el.value === "" ? null : parseFloat(el.value);
        else if (type === "entities") {
          const vals = Array.from(el.selectedOptions).map((o) => o.value).filter(Boolean);
          changes[key] = vals;
        } else if (type === "entity") changes[key] = el.value || null;
        else changes[key] = el.value;
      }
      try {
        await this._hass.callWS({ type: "kd_brain/config/update", changes });
        this._toastMsg("Opgeslagen ✓");
        setTimeout(() => this._loadConfig(), 800);
      } catch (e) {
        this._toastMsg("Opslaan mislukt: " + (e && e.message ? e.message : "onbekend"));
      }
    });
  }

  // ---- SVG chart primitives ----------------------------------------------

  _svgLine(seriesList, opts) {
    opts = opts || {};
    const w = 500, h = 200, pad = 30;
    let allV = [], allT = [];
    for (const s of seriesList) for (const p of s.points) { allV.push(p.v); allT.push(p.t.getTime()); }
    if (!allV.length) return `<div class="muted">Geen data.</div>`;
    const yMin = opts.yMin != null ? opts.yMin : Math.min(...allV);
    const yMax = opts.yMax != null ? opts.yMax : Math.max(...allV);
    const ySpan = yMax - yMin || 1;
    const tMin = Math.min(...allT), tMax = Math.max(...allT), tSpan = tMax - tMin || 1;
    const sx = (t) => pad + ((t - tMin) / tSpan) * (w - 2 * pad);
    const sy = (v) => h - pad - ((v - yMin) / ySpan) * (h - 2 * pad);
    let paths = "";
    for (const s of seriesList) {
      const d = s.points.map((p, i) => `${i ? "L" : "M"}${sx(p.t.getTime()).toFixed(1)} ${sy(p.v).toFixed(1)}`).join(" ");
      paths += `<path d="${d}" fill="none" stroke="${s.color}" stroke-width="2"/>`;
    }
    const zero = yMin < 0 && yMax > 0 ? `<line x1="${pad}" y1="${sy(0)}" x2="${w - pad}" y2="${sy(0)}" stroke="#fff" opacity=".25"/>` : "";
    const axis = `<text x="${pad}" y="14" font-size="10" fill="#fff" opacity=".6">${yMax.toFixed(0)}${opts.unit || ""}</text>
      <text x="${pad}" y="${h - pad + 14}" font-size="10" fill="#fff" opacity=".6">${yMin.toFixed(0)}${opts.unit || ""}</text>`;
    return `<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Tijdreeks">${zero}${paths}${axis}</svg>`;
  }

  _legend(series) {
    return `<div style="margin-top:8px">${series.map((s) => `<span class="chip" style="border-left:3px solid ${s.color}">${s.label || ""}</span>`).join("")}</div>`;
  }

  _svgBars(groups, keys, colors, labels) {
    const w = 500, h = 220, pad = 34;
    let maxV = 0;
    for (const g of groups) for (const k of keys) maxV = Math.max(maxV, g[k] || 0);
    maxV = maxV || 1;
    const gw = (w - 2 * pad) / groups.length;
    const bw = (gw * 0.8) / keys.length;
    let bars = "";
    groups.forEach((g, gi) => {
      keys.forEach((k, ki) => {
        const v = g[k] || 0;
        const bh = (v / maxV) * (h - 2 * pad);
        const x = pad + gi * gw + gw * 0.1 + ki * bw;
        const y = h - pad - bh;
        bars += `<rect x="${x}" y="${y}" width="${Math.max(bw - 1, 1)}" height="${bh}" fill="${colors[ki]}"/>`;
      });
      bars += `<text x="${pad + gi * gw + gw / 2}" y="${h - pad + 14}" text-anchor="middle" font-size="10" fill="#fff" opacity=".6">${g.label}</text>`;
    });
    const legend = labels.map((l, i) => `<span class="chip" style="border-left:3px solid ${colors[i]}">${l}</span>`).join("");
    return `<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Week-energie">${bars}
      <text x="${pad}" y="14" font-size="10" fill="#fff" opacity=".6">${maxV.toFixed(1)} kWh</text></svg>
      <div style="margin-top:8px">${legend}</div>`;
  }
}

customElements.define("kd-brain-panel", KdBrainPanel);
