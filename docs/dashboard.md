# Auto-generated dashboard

KD Brain can build a Lovelace dashboard from whichever entities you've actually
configured, so the layout always matches your setup (no empty cards for
devices you haven't wired up).

## Usage

1. Go to **Developer tools → Actions** (or **Services**).
2. Call `kd_brain.generate_dashboard`. Leave `entry_id` empty if you only have
   one KD Brain config entry.
3. Enable "response data" / read the response — it returns a `dashboard` object
   with `title` and `views` (standard Lovelace view/card structure).
4. Create a new dashboard (**Settings → Dashboards → Add dashboard**), switch
   it to **YAML mode**, and paste the `views` list under a `views:` key.

## What gets included

The dashboard groups entities into sections — Prices, Telemetry, Optimisation,
Control & safety, EV charging, Heat pump — and only includes a section when at
least one of its entities is actually registered for the config entry. A
history-graph card is added for the price-curve sensor when it's enabled.

Sections and layout are a starting point: once created, the dashboard is a
normal Lovelace dashboard and can be edited like any other.
