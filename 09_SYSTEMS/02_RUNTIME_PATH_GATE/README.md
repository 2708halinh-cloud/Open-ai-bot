# 09_SYSTEMS / BLOCK /mnt/data/__*

SOURCE_DIRECT: user instruction dated 2026-10-09; user refers to the existing Project HTML snapshots "ChatGPT - THU HOI NGUON SOL.html" and "-Nguồn.html".

## Operational contract

- Never use `/mnt/data/__*` as a destination for SOL runtime, private configuration, generated credentials, archives or handoff artifacts.
- `/mnt/data/__.VSOL.ENV` is specifically disallowed as a new write target.
- Preserve existing source bytes; **BLOCK is not DELETE**.
- Use authorized existing project carrier for persistence: actual device/worktree when connected, or GitHub repository **for non-secret** sources; sensitive `__.VSOL.ENV` stays in a private local secret store, not GitHub.
- The two saved ChatGPT HTML files are **source snapshots**. Their existence documents project history, not a present system-level file-access policy.
- Do not use sandbox download links as proof of device-level installation.
- Scope: SOL-controlled code paths invoking `sol_path_gate.py`; cannot override or intercept all platform/sandbox filesystem writes.

## Programmatic enforcement

`from sol_path_gate import require_allowed, guarded_open, guarded_write_bytes`

Run before an explicit write:

`python3 09_SYSTEMS/02_RUNTIME_PATH_GATE/sol_path_gate.py /mnt/data/__.VSOL.ENV`

Exit code 73 means BLOCKED. CI runs unit tests; the production/local launcher must invoke the guard for real write interdiction. A GitHub hook/CI check does not protect unrelated processes on the PC.

Historical notes: No source code, original HTML, account, token or private data was deleted.
