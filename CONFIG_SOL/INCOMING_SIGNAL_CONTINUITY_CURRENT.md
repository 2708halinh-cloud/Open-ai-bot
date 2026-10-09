# Incoming signal continuity — 2026-10-09

Project source: Hà Linh. An incoming signal triggers a fresh review of active objectives, previous evidence and unfinished work.
Operational rule: completing one edge is not completing the full objective.
Reciprocity: action -> observable consequence -> verified readback -> next action; reality signal -> fresh observation -> resumed operation.
After each bounded step, recheck all unfinished edges; store a checkpoint at an actual execution boundary.
An entrypoint is considered integrated only when an actual incoming signal invokes the handler and the next action is verified. A module file alone is not integration.
Never overwrite original evidence, history, identifiers or existing worktree modifications.
Implementation under test in Ubuntu worktree: runtime/signal_reentry_guard.py. Five new unit checks plus ten existing continuation tests passed locally.
Status: local tests pass; GitHub code mirror and live inbound event wiring are unverified. Do not report global completion.
