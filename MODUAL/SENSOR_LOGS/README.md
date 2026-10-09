# MODUAL / SENSOR_LOGS — GitHub Current State

SOURCE_DIRECT: D:\SENSOR_LOGS

- _SESORIMOTOR__WINDOWS__XIAOMI12__REDMINOTE14PRO__0000THEMASTERTEACHER__R000_075203003486__.CSV: bulk telemetry local carrier. Raw bytes remain on local/bulk storage; GitHub keeps digest + header + latest row.
- _SESORIMOTOR__{WINDOWS)__XIAOMI12__REDMINOTE14PRO__0000THEMASTERTEACHER__R000_075203003486__.CSV: live/intermediate MODUAL parameter carrier; copied into live/.
- source/: executable control files that generate/sync MODUAL state.
- MODUAL_PARAMETER_CURRENT.json: current compact state/readback.

AUTO_SYNC:
D:\SENSOR_LOGS\telemetry_buffer_sync.py calls modual_github_sync.py on the same snapshot cadence.

GitHub is used here as Law/State, not as the bulk telemetry store.
