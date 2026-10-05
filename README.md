# MAK Grill — Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/v/release/papac0rn/ha-mak-grill)](https://github.com/papac0rn/ha-mak-grill/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-papac0rn-orange?logo=buy-me-a-coffee)](https://buymeacoffee.com/papac0rn)

Local-push Home Assistant integration for **MAK Pellet Boss WiFi** grills. No cloud dependency — the grill talks directly to your HA instance over your LAN.

> **MAK Grills has closed its doors**, but your grill still works. This integration keeps your Pellet Boss WiFi connected — locally, forever — with no cloud required.

## How it works

The Pellet Boss WiFi controller POSTs telemetry to `makgrillsmobile.com` every few seconds while running. This integration registers that same HTTP endpoint on your Home Assistant instance. A local DNS rewrite redirects the grill's traffic to HA instead of the (now-defunct) MAK cloud, giving you real-time local control with zero internet dependency.

```
┌──────────┐   POST /GrillService/Service   ┌──────────────────┐
│ MAK Grill │ ─────────────────────────────► │ Home Assistant    │
│ Pellet    │ ◄───────────────────────────── │ (your LAN)       │
│ Boss WiFi │   setPoint, cookMode, power    │                  │
└──────────┘                                 └──────────────────┘
     DNS rewrite: makgrillsmobile.com → your HA IP
```

## Screenshots

<p align="center">
  <img src="images/dashboard.png" alt="MAK Grill Dashboard - Controls" width="350"/>
  &nbsp;&nbsp;
  <img src="images/dashboard-history.png" alt="MAK Grill Dashboard - History & Diagnostics" width="350"/>
</p>

## Features

- **Real-time telemetry** — pit temp, 3 meat probes, power state, grill flags
- **Full control** — setpoint, cook mode (Smoke/Grill/Sear), zone probe, power on/off
- **Safety** — flameout detection, cooldown interlock, auto-sync setpoint from pit temp
- **Diagnostics** — last seen timestamp, POST count, grill ID, raw flags
- **Local push** — no polling, no cloud, no latency
- **60-second timeout** — no more flickering disconnected status between slow POSTs

## Entities

| Entity | Type | Description |
|--------|------|-------------|
| Pit Temperature | Sensor | Current grill temperature (°F) |
| Probe 1 / 2 / 3 | Sensor | Meat probe temperatures (°F) |
| Power State | Sensor | Reported power state from grill |
| Grill ID | Sensor | Grill serial identifier |
| Flags | Sensor | Raw grill status flags |
| Last Seen | Sensor | Timestamp of last grill POST |
| Post Count | Sensor | Total POSTs received this session |
| Connected | Binary Sensor | Whether the grill is actively posting |
| Flameout | Binary Sensor | Flameout detection (once up to temperature, pit stays 35°F below the setpoint, capped at 450°F, for 8 min; or the pit never comes up to temperature within 45 min) |
| At Setpoint | Binary Sensor | Grill has reached target temperature |
| Setpoint | Number | Target temperature (150–500°F, writable) |
| Power | Switch | Power on/off (with cooldown interlock) |
| Cook Mode | Select | Smoke / Grill / Sear |
| Zone Probe | Select | Which probe controls the zone |
| Create Dashboard | Button | One-press setup — creates a complete MAK Grill dashboard in your sidebar |

## Dashboard

After installing, go to **Settings → Devices → MAK Grill** and press the **Create Dashboard** button. A fully configured dashboard appears in your sidebar with pit temperature gauge, controls, probes, cook history graph, status, and safety/diagnostics cards.

Want to build your own instead? See the [Dashboard Guide](https://github.com/papac0rn/ha-mak-grill/wiki/Dashboard-Guide) for copy-paste YAML for each card.

## Installation

### HACS (recommended)

1. Open HACS in Home Assistant
2. Click the three dots menu → **Custom repositories**
3. Add `https://github.com/papac0rn/ha-mak-grill` with category **Integration**
4. Search for "MAK Grill" and install
5. Restart Home Assistant

### Manual

Copy the `custom_components/mak_grill` folder to your Home Assistant `config/custom_components/` directory and restart.

## Setup

### 1. DNS rewrite

Point `makgrillsmobile.com` to your Home Assistant IP on your router. The Pellet Boss controller resolves this hostname to find its server.

**Example (TP-Link Omada / ER8411):**
- Go to your router's DNS settings
- Add a static DNS entry: `makgrillsmobile.com` → `192.168.1.200` (your HA IP)

**Example (Pi-hole / AdGuard Home):**
- Add a DNS rewrite: `makgrillsmobile.com` → your HA IP

**Pro tip:** If your grill is on a separate IoT VLAN, consider adding a firewall rule to block the grill from reaching external DNS servers. This forces it to use your router's DNS (with the rewrite) and makes the connection bulletproof.

### 2. Add the integration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **MAK Grill**
3. Enter a name for your grill
4. Done — entities appear immediately

### 3. Verify

Power on your grill. Within a few seconds, `binary_sensor.mak_grill_connected` should turn ON and temperature sensors should populate.

You can also test with curl:

```bash
curl -X POST -d "GrillId=TEST&Temp=275&Power=ON&Probe1=165&Probe2=0&Probe3=0&GrillFlags=ATSET" http://YOUR_HA_IP/GrillService/Service
```

## Protocol

The Pellet Boss WiFi controller sends form-encoded POSTs with these fields:

| Field | Description |
|-------|-------------|
| GrillId | Grill serial number |
| Temp | Pit temperature (°F) |
| Power | Power state (ON/OFF/COOL/CD) |
| Probe1–3 | Meat probe temperatures (°F) |
| GrillFlags | Status flags (e.g., ATSET) |

The integration responds with a quoted command string that sets the grill's operating parameters:

```
"setPoint=225&potStatus=&cookMode=1&zoneProbe=1&power=1"
```

## Safety features

- **Auto-sync setpoint**: On first connection, the integration syncs the HA setpoint to the grill's actual pit temperature — no more accidentally commanding 500°F when the grill is at 225°F
- **User-set tracking**: The integration only sends commands you explicitly set in HA. It never overrides the grill's own settings unless you ask it to.
- **Cooldown interlock**: You can't power on a grill that's in cooldown mode
- **Flameout detection**: Once the grill has come up to temperature, alerts if the pit stays 35°F+ below the setpoint for 8 minutes. A MAK holds about 450°F at most, so a higher setpoint is judged against 450°F. A cook that never reaches temperature within 45 minutes (a failed light) also counts as a flameout.

## Phone alert when the grill is up to temp

`binary_sensor.mak_grill_at_setpoint` follows the grill's own `ATSET` flag. A grill set above about 450°F may never report it, so the example below also fires when the pit gets within 5°F of the setpoint (capped at 450°F).

It sends one alert per setpoint per cook, so lid-open dips on a long smoke don't re-alert. Create a toggle helper named **MAK Grill set point alert sent** first, then replace `mobile_app_your_phone` with your phone's notify service. On Android, `channel: alarm_stream` makes it beep even when the phone is on silent.

```yaml
alias: MAK Grill - at set point alert
mode: queued
triggers:
  - trigger: state
    entity_id: sensor.mak_grill_power_state
    from: "OFF"
    not_to: [unknown, unavailable]
    id: rearm
  - trigger: state
    entity_id: number.mak_grill_setpoint
    not_from: [unknown, unavailable]
    not_to: [unknown, unavailable]
    for: { seconds: 15 }
    id: rearm
  - trigger: state
    entity_id: binary_sensor.mak_grill_at_setpoint
    from: "off"
    to: "on"
    id: atset
  - trigger: template
    value_template: >
      {% set raw = states('number.mak_grill_setpoint') | float(0) %}
      {% set sp = [raw, 450] | min %}
      {{ raw >= 160 and is_state('sensor.mak_grill_power_state', 'ON')
         and states('sensor.mak_grill_temperature') | is_number
         and (states('sensor.mak_grill_temperature') | float) >= sp - 5 }}
    for: { seconds: 30 }
    id: temp
actions:
  - choose:
      - conditions:
          - condition: trigger
            id: rearm
        sequence:
          - action: input_boolean.turn_off
            target: { entity_id: input_boolean.mak_grill_set_point_alert_sent }
      - conditions:
          - condition: trigger
            id: [atset, temp]
          - condition: state
            entity_id: sensor.mak_grill_power_state
            state: "ON"
          - condition: state
            entity_id: input_boolean.mak_grill_set_point_alert_sent
            state: "off"
        sequence:
          - action: input_boolean.turn_on
            target: { entity_id: input_boolean.mak_grill_set_point_alert_sent }
          - action: notify.mobile_app_your_phone
            data:
              title: MAK Grill is up to temp
              message: >
                Pit {{ states('sensor.mak_grill_temperature') | float(0) | round(0) | int }}°F
                (setpoint {{ states('number.mak_grill_setpoint') | int(0) }}°F)
              data:
                ttl: 0
                priority: high
                channel: alarm_stream
                tag: mak_grill_setpoint
```

## What's new

| Version | Changes |
|---------|---------|
| **v1.3.2** | Flameout no longer false-alarms while the grill warms up: it only counts once the pit has reached temperature. A setpoint above 450°F is judged against 450°F, what a MAK actually holds. A cook that never comes up to temperature within 45 minutes is reported as a flameout. README adds an example "up to temp" phone alert |
| **v1.3.1** | Honest temperatures: pit and probe sensors read unknown (not 0°F or a frozen last value) when the grill is off or disconnected, and unplugged probes read unknown instead of 0°F. Dashboard shows a status card in place of the gauge while the grill is off. Power switch now reflects the grill's real state (including ignition) |
| **v1.3.0** | Create Dashboard button — one-press sidebar dashboard setup; gauge shows 0°F instead of error when grill offline |
| **v1.2.0** | Flameout detection, at-setpoint indicator, 60-second timeout, auto-sync setpoint on first connection |
| **v1.1.0** | Full grill control — setpoint, cook mode, zone probe, power switch with cooldown interlock |
| **v1.0.0** | Initial release — local-push telemetry, temperature sensors, connection status |

## Works well with

- **[Grill Buddy](https://github.com/jeroenterheerdt/grillbuddy)** — "Alert me when probe 1 hits 203°F" — works with any HA temperature sensor, including the ones this integration provides
- **[meater-in-local-haos](https://github.com/R00S/meater-in-local-haos)** — Local-first cooking assistant for HA with guided cooks, AI recipe building, and cook history — just point it at your MAK Grill probe entities

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| Grill not connecting / entities stay "unknown" | DNS rewrite not set up or not resolving | Verify `makgrillsmobile.com` resolves to your HA IP: `nslookup makgrillsmobile.com` from the grill's network |
| Entities show "unknown" but grill is on | Grill hasn't sent its first POST yet | Wait 10–15 seconds after power-on; check `binary_sensor.mak_grill_connected` |
| Flameout comes on while the grill is still heating up | v1.3.1 and earlier started the 8-minute flameout timer as soon as the grill reached ON, before it was up to temperature | Fixed in v1.3.2. Update through HACS |
| Flameout stays on with a setpoint above 450°F | v1.3.1 and earlier compared the pit to the full setpoint, which a MAK can't hold | Fixed in v1.3.2, which judges against 450°F |
| Temperatures read "unknown" | Grill is powered off or disconnected, or the probe is unplugged | Expected behavior (v1.3.1+). The generated dashboard hides the gauge and shows Connected / Power State until the grill posts again |
| Grill on different VLAN can't reach HA | Firewall blocking cross-VLAN traffic on port 80 | Add a firewall rule allowing the grill's subnet to reach HA's IP on port 80 |

For more help, see the [Troubleshooting wiki page](https://github.com/papac0rn/ha-mak-grill/wiki/Troubleshooting) or [open an issue](https://github.com/papac0rn/ha-mak-grill/issues).

## Credits

- **[bawilson2](https://github.com/bawilson2)** — Original protocol reverse-engineering and [mak-controller](https://github.com/bawilson2/mak-controller) Docker container that proved local control was possible. This integration wouldn't exist without that groundwork.
- Built with [Claude Code](https://claude.com/claude-code)

## License

MIT
