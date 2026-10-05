DOMAIN = "mak_grill"

DEFAULT_NAME = "MAK Grill"

CONF_GRILL_NAME = "grill_name"

GRILL_TIMEOUT_SECONDS = 60.0
FLAMEOUT_THRESHOLD_F = 35
FLAMEOUT_DURATION_SECONDS = 480
# A MAK holds about 450°F at most even when the setpoint is higher, so flameout is
# judged against min(setpoint, FLAMEOUT_MAX_HOLD_F)
FLAMEOUT_MAX_HOLD_F = 450
# Time allowed to come up to temperature before a cook that never gets there is a flameout
FLAMEOUT_WARMUP_GRACE_SECONDS = 2700

COOK_MODES = {
    1: "Smoke",
    2: "Grill",
    3: "Sear",
}

ZONE_PROBES = {
    1: "Probe 1",
    2: "Probe 2",
    3: "Probe 3",
}
