# MAK Grill — Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Local-push Home Assistant integration for **MAK Pellet Boss WiFi** grills. No cloud dependency — the grill talks directly to your HA instance over your LAN.

## How it works

The Pellet Boss WiFi controller POSTs telemetry to `makgrillsmobile.com/GrillService/Service` every few seconds while the grill is running. This integration registers that same HTTP endpoint on your Home Assistant instance. A local DNS rewrite redirects the grill's traffic to HA instead of the MAK cloud, giving you real-time local control.

## Entities

| Entity | Type | Description |
|--------|------|-------------|
| Pit Temperature | Sensor | Current grill temperature (°F) |
| Probe 1 / 2 / 3 | Sensor | Meat probe temperatures (°F) |
| Power State | Sensor | Reported power state from grill |
| Grill ID | Sensor | Grill serial identifier |
| Flags | Sensor | Raw grill status flags |
| Connected | Binary Sensor | Whether the grill is actively posting (15s timeout) |
| Flameout | Binary Sensor | Flameout detection (pit temp stays 35°F below setpoint for 8 min) |
| At Setpoint | Binary Sensor | Grill has reached target temperature |
| Setpoint | Number | Target temperature (150–500°F, writable) |
| Power | Switch | Power on/off (with cooldown interlock) |
| Cook Mode | Select | Smoke / Grill / Sear |
| Zone Probe | Select | Which probe controls the zone |

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

## Credits

- Protocol based on [mak-controller](https://github.com/bawilson2/mak-controller) by @bawilson2
- Built with [Claude Code](https://claude.com/claude-code)

## License

MIT
