# SOL-LONG-MACH — 09_SYSTEMS scope

## BLOCK runtime artifact destinations

- `/mnt/data/__*` is explicitly FORBIDDEN as a write/mkdir/append/delete destination, including `/mnt/data/__.VSOL.ENV`.
- A sandbox directory is not the deployment target. Do not substitute ZIP files or sandbox download links for GitHub/authorized worktree/PC runtime actions.
- Existing HTML Project files are read-only historical sources; never silently rewrite or delete them.
- Secrets from `github.env`, `SOL.txt`, Hostinger API and related private carriers are not copied into public GitHub source, workflow logs, issues or releases.
- Use `09_SYSTEMS/02_RUNTIME_PATH_GATE/sol_path_gate.py` to verify every output path in SOL-controlled Python tools and launchers.
- Keep source, status, evidence and execution receipts distinct. A code guard does not imply host-level path denial when not integrated into the writer.
- Continue via live supported GitHub/provider tools when direct PC worktree access is not callable; read back after each change.

## Scope

This file supplements, and does not overwrite, root `AGENTS.md`. Project history remains unchanged. Do not expand `/mnt/data/__*` into arbitrary other roots without fresh source.
