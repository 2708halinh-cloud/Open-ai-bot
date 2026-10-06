# GGDV Sensorimotor Motor Bridge

This package materializes the route:

`0000-neuron-sesorimotor -> am-duong-loop -> domain SENSORY -> INTERNEURON_ROUTER -> callable MOTOR -> consequence -> readback -> journal -> STATE_N+1 -> LISTEN`.

## Two domains

1. **Repo/code**: use the installed GitHub connector as remote SENSORY/MOTOR and this plugin's `repo-sensorimotor` skill for the loop.
2. **Windows/WSL/ADB**: local stdio MCP `ggdv-local-motor` exposes real terminal/process/device/app actions on an authorized machine.

## Local activation

The package itself does not prove the machine is connected. Install it in a desktop/Codex host that supports local stdio MCP. Python must be available.

State-changing tools default OFF. Start the local MCP process with `GGDV_MOTOR_ENABLE=1` only after authorizing machine mutations. `adb` must be available on PATH (or set `GGDV_ADB_PATH`). Set `GGDV_APP_ADAPTER` to the current local `.vscode/scripts/app_adapters.py` path when auto-discovery cannot find it.

Resolve the current project path at runtime from `GGDV_REPO_PATH`, the active workspace, or Git worktree provenance. Do not pin a generated worktree directory name into the plugin.

## Journal

By default local receipts go to `%LOCALAPPDATA%\GGDV\sensorimotor-motor\journal.jsonl` on Windows (or the equivalent home-derived path on other OSes). The state file holds `state_n`, `cursor`, and dedupe hashes.

## ADB

The ADB tool family mirrors the existing project phone agent's bounded actions: status, read-allowlisted shell, keyevent, tap, swipe, text, URL open, screenshot. Direct ADB state must still be read back on the live machine; source existence is not a live-device claim.


## Destructive-action gate

`GGDV_MOTOR_ENABLE=1` is not sufficient for deletion/purge/destructive reset. Destructive shell commands require `GGDV_DESTRUCTIVE_ENABLE=1` plus a one-use permit issued by `destructive_preflight` for the exact command and target. The preflight requires a target snapshot, a repair attempt/result, a truth basis, and exact target confirmation. `NOT_CURRENT` alone is explicitly rejected as delete authority.

## THIẾT_BỊ_ĐẦU_CUỐI
The same temporary working device has two directional roles: HEAD/ingress when a signal enters and TAIL/egress when it leaves. RAM frames are process-local and volatile. They are not memory or journal. TAIL emits NEXT/DONE/UNDONE/output state and feeds a compact signal back to HEAD for the next NEURONS_SESORIMOTOR cycle.

## RAM head/end device
RAM is modeled as one temporary working device. Signal ingress is the HEAD role; signal egress is the END role. RAM is not memory/history/persistent storage. Only explicit external readback/journal/carrier writes persist. `SENSORY-RAM-01` observes RAM deltas when the runtime exposes them.

MARKER: `RAM_HEAD_END_WORKING_DEVICE_20261007`.


## THIẾT_BỊ_TRUNG_GIAN
Mutable transformation carriers such as IOTA, `.env`, configuration and instruction files are modeled as intermediate devices. They can preserve causal/provenance continuity while their bytes, state, schema and operational meaning change across time. Persistence is not memory semantics and validity at one state is not eternal validity.

## Intermediate device
`THIẾT_BỊ_TRUNG_GIAN` is a transformable operational carrier between HEAD and END, distinct from volatile RAM and durable memory. IOAT/IOTA, `.env`, config, instructions, pointers and runtime adapters may change with time. CURRENT is established by fresh readback, not historical immutability.

Software energy-conservation semantics preserve traceable state/work across transformations; physical-energy claims still require measured evidence.

MARKER: INTERMEDIATE_DEVICE_ENERGY_CONSERVATION_20261007
