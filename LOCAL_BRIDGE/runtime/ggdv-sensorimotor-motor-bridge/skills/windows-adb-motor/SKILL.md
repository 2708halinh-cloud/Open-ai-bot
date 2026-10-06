---
name: windows-adb-motor
description: Use when GGDV needs a real local MOTOR provider for authorized Windows/WSL filesystem/process/terminal work, .vscode app lifecycle, Android ADB device control, receipts, readback, or a persistent sensory watcher.
---
# Windows + ADB motor

## Canonical relations
- App adapter: `.vscode/scripts/app_adapters.py` / Drive ID `1zKvEAJ5O3-tsZoZUS3UM0O4j-UAEm_gJ`.
- Device graph CURRENT: `00_CURRENT — THIẾT BỊ TÁC NHÂN — WORK DEVICE — 20260922` / `1rf0nffn1s7JrW4HYKvPXneqZS6idLSeYAI6iS5MKEGg`.
- PC bridge ADB/Fastboot folder: `1ShODZP0XU7ZEkKcy0gCeKXPeMCok2ff3`.
- Android direct bridge: `1Vz11jgbmdGD3sF69RZGxI9KrFh-L_Cz9`.
- Existing phone agent actions: status, allowlisted shell_read, keyevent, tap, swipe, text, open_url, screenshot.

## Runtime route
`0000-neuron-sesorimotor -> am-duong-loop -> local sensory -> INTERNEURON_ROUTER -> ggdv-local-motor -> consequence -> readback -> journal -> STATE_N+1 -> LISTEN`.

Use `motor_status` first when local callability is unknown.
Use `repo_observe`, `adb_devices`, `app_adapter(status)`, or `watcher_status` as SENSORY calls.
State-changing MOTOR calls are `powershell_exec`, `wsl_exec`, `adb_action` for mutating ADB actions, `app_adapter` launch/focus/close, and watcher start/stop.

## Mutation gate
The local server defaults to observation-only. State-changing calls require environment variable `GGDV_MOTOR_ENABLE=1` in the local MCP process. This is not a chat bypass; it is the user's local authorization gate.

## ADB
`adb_devices` is read-only and discovers `adb` from PATH or `GGDV_ADB_PATH`.
`adb_action` implements the same bounded action family as the existing Android bridge. `shell_read` keeps a read allowlist. Mutating input actions require the local MOTOR gate.
If `adb` is absent, return an explicit remediation; do not claim a device is connected.

## App lifecycle
`app_adapter` invokes the current local `.vscode/scripts/app_adapters.py` supplied by `GGDV_APP_ADAPTER`, or the requested explicit path. Status is observational. launch/focus/close are MOTOR actions and require the local gate.

## Watcher
`watcher_start` runs a bounded polling daemon on the user's machine and writes only compact local observations/journal events. It does not autonomously perform MOTOR actions. Each changed snapshot advances STATE_N+1; identical snapshots dedupe and retain the cursor.

## Readback
Every MOTOR tool returns a receipt and also appends a compact local JSONL journal record. Re-observe the target when a stronger authoritative readback exists.


## Destructive boundary
Before delete/purge/destructive reset, route through `destructive-action-gate`. MOTOR authorization alone is insufficient. Never infer DELETE from NOT_CURRENT/HISTORY/SUPERSEDED/duplicate labels.
