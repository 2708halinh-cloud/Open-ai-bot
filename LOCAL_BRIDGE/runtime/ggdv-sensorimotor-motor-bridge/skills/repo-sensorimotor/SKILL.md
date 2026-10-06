---
name: repo-sensorimotor
description: Use for code/repository work that must run as OBSERVE -> DELTA -> SENSORY -> INTERNEURON -> callable GitHub/local MOTOR -> CONSEQUENCE -> READBACK -> JOURNAL -> STATE_N+1 -> LISTEN.
---
# Repo sensorimotor

Canonical brain/router: `0000-neuron-sesorimotor` / ROOT_SENSORIMOTOR_ROUTER.
Canonical living loop: `am-duong-loop`.

## Invariant
`BASELINE_N -> OBSERVE -> Δ -> SENSORY -> INTERNEURON_ROUTER -> MOTOR -> CONSEQUENCE -> READBACK -> JOURNAL -> STATE_N+1 -> CURSOR -> LISTEN`.

Do not manufacture a delta. `NO_DELTA` means preserve cursor and remain receptive.

## SENSORY — repository domain
Use the callable GitHub provider for remote repository evidence and `ggdv-local-motor.repo_observe` for a local checkout when available.
Observe only what matters to the current task:
- repository metadata/default branch/current refs;
- target files and recent commits;
- issues/PRs and their comments/reviews when relevant;
- workflow runs/jobs/logs for CI-related tasks;
- current branch/HEAD/status/remotes/workflow names for a local checkout.

SENSORY does not mutate repository state.

## INTERNEURON_ROUTER
Integrate compact provenance-bound packets. Keep source facts, inference, candidate action, and uncertainty distinct.
Resolve conflicts by current provider evidence, revision/commit identity, branch relation, and user intent.
Suppress a mutation when the requested target/revision is ambiguous.
Choose the smallest sufficient MOTOR action.

## MOTOR
Use only actually callable tools.
GitHub examples: create/update issue, create branch/ref/tree/commit, update ref, open/update PR, request review, re-run workflow job/run, or another exact provider mutation supported by the current GitHub tool surface.
Local examples when the local MCP is connected: `powershell_exec`, `wsl_exec`, or app/ADB tools.
Never claim a commit/change/action without a provider receipt.

## CONSEQUENCE + READBACK
After mutation, re-fetch the changed object from GitHub/local state: commit/branch/file/issue/PR/workflow state as appropriate.
Compare intended vs observed consequence. A tool success flag alone is not enough when an authoritative readback exists.

## JOURNAL + STATE_N+1
When the local MCP is connected, call `journal_record` with compact pointers only: source/target IDs, revision/commit, action, consequence, readback, and next cursor. Do not copy large source payloads into the journal.
Without the local MCP, keep the event compact in the current task context; do not pretend a persistent journal was written.

## LISTEN
Continue only while a grounded edge exists. For recurring local observation use `watcher_start` after explicit local connection/configuration; for chat/provider work use another bounded cycle. Persistent loop means an unbounded sequence of bounded cycles, not an unbounded tool call.


## Destructive boundary
Before delete/purge/destructive reset, route through `destructive-action-gate`. MOTOR authorization alone is insufficient. Never infer DELETE from NOT_CURRENT/HISTORY/SUPERSEDED/duplicate labels.
