# KD Brain custom panel

After the integration is set up, KD Brain adds a **KD Brain** entry to the Home
Assistant sidebar: a self-contained dashboard where you can see what your energy
system is doing and change every setting in one place.

## What you get

Five tabs:

- **Overzicht** — system status (control mode, active strategy, recommended
  action, battery SOC/power), a live **energy-flow** diagram (grid / solar /
  home / battery / EV / heat pump with animated flows), today's price summary,
  and weekly-energy bars.
- **Prijzen** — the all-in price curve for today and tomorrow, with cheap hours
  (below your threshold) in green, expensive hours (above the daily average) in
  red, and the current interval highlighted.
- **Batterij** — state-of-charge over the last 24 h, a power timeline
  (grid / solar / battery) and per-battery detail.
- **EV & WP** — EV smart-charging and heat-pump status with the reasoning behind
  each recommendation.
- **Instellingen** — the full configuration (tariff, devices/sensors,
  strategies & economics, control & safety, EV, heat pump). Changes are saved
  straight from the panel and reload the integration.

## How it works

The panel is a single vanilla-JavaScript web component served as a static asset
and registered with `panel_custom` — there is no build step and no external
chart library, so it works fully offline and ships cleanly through HACS.

Data comes from three sources:

- Live values via the integration's `kd_brain/snapshot` websocket command.
- Time-series charts via Home Assistant's built-in history websocket, reading
  the source sensors you configured (grid, solar, battery).
- Settings via `kd_brain/config/get` and `kd_brain/config/update`. Writing
  settings requires an admin user.

> The weekly-energy bars are an approximation: they integrate the configured
> power sensors over time rather than reading dedicated kWh meters.

## Notes

- The panel styles itself from your active Home Assistant theme.
- If you don't see it in the sidebar after install, reload the integration or
  refresh the browser (the panel module is versioned to bust the cache).
- You can still build your own Lovelace dashboard from KD Brain's entities if
  you prefer one; the panel complements rather than replaces standard dashboards.
