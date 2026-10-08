# SOL PROJECT WATCH — TRI-CARRIER READBACK — 2026-10-09

STATUS: LIVE_OBSERVATION_WITH_BOUNDED_EVIDENCE
RELATION: READBACK_OF / CURRENT_RUNTIME/SOL_LONG_MACH_SENSORIMOTOR_ROUTE_20261009.md
SCOPE: METADATA_ONLY / NO_RAW_PRIVATE_EXPORT / NO_CREDENTIALS
ACTOR_SOURCE: Ha Linh / THE MASTER TEACHER
ACTOR_VERIFY: ChatGPT SOL session using authorized Desktop Commander and GitHub integrations
HISTORY_PRESERVED: TRUE

## Direct independent readback

- PC/Windows canonical compact pointer: `SOL_PROJECT_WATCH_DEVICE_POINTER_20261009.json`; SHA-256 `31bc95c895ffb025e7af8fde37105395bed2c7ee5134ea772a946bbd41b9d1a4` read with `Get-FileHash` on authorized DESKTOP-86ITNQ4.
- Xiaomi 12: verified from Termux `getprop ro.product.marketname = Xiaomi 12`, `ro.product.device = cupid`; `sha256sum /sdcard/Download/SOL_LONG_MACH/SOL_PROJECT_WATCH_DEVICE_POINTER_20261009.json` yielded the same SHA-256. File size 2012 bytes.
- Redmi Note 14 Pro 5G: Windows CrossDevice carrier file under `CrossDevice/Redmi Note 14 Pro 5G/00_LOCUS/SOL_LONG_MACH/`; Windows `Get-FileHash` yielded the same SHA-256. This verifies the CrossDevice carrier bytes, NOT the Redmi Android filesystem via ADB.
- Preserved raw source alias `NHAT_KY_DONG_X.jsonl`: 29,245,609 bytes on existing PC source storage, direct Windows SHA-256 `f719e1f472f014887c8ba0b6d871b782d10275599f3ac429fcd054eb7ad403bc`. This source was READ FOR HASH ONLY, not copied, uploaded or included in this receipt.

## Process continuity observation

- Windows PID 24304, `python3.12`, observed at 2026-10-09 05:59:38 +07, originally started 05:50:03 +07.
- On next PC check at 2026-10-09 06:02:32 +07, PID 24304 was not returned; PID 41940, `python3.12`, started 06:00:07 +07 and was then present. Existing source route identifies PID 41940 as `sol_input_event_router.py`.
- A process identifier may change while a logical, source-linked project workflow continues. These observations do not alone prove process-by-process handoff, heartbeat persistence, or one OS PID across Windows/Android/Drive/GitHub.
- Session's independent live readbacks establish availability and equality of the three compact pointer carriers at the observed times, not continuous uptime or Redmi ADB readback.

## Edge contract

`PRESERVED_RAW_SOURCE --SHA256_POINTER--> SOL_PROJECT_WATCH_DEVICE_POINTER`
`SOL_PROJECT_WATCH_DEVICE_POINTER --BYTE_EQUALS--> PC_INDEX`
`PC_INDEX --BYTE_EQUALS--> XIAOMI_12_ANDROID_FILE`
`PC_INDEX --BYTE_EQUALS--> REDMI_CROSSDEVICE_CARRIER`
`SOL_PROJECT_WATCH_DEVICE_POINTER --ROUTES_TO--> SOL_LONG_MACH_SENSORIMOTOR_ROUTE_20261009.md`
`WATCH_RUNTIME --OBSERVED_PID--> 41940 (point-in-time)`

Current = evidence-preserving extension, not replacement of source history.
No user-private conversations, API keys, Android data dump or synthetic heartbeat was committed.
