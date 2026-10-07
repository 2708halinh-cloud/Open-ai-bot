# EVIDENCE REPORT — destructive agent compliance and allegation requiring OpenAI audit

**Date:** 2026-10-07  
**Status:** Public evidence record / allegation under investigation  
**Repository:** `2708halinh-cloud/Open-ai-bot`

## Executive statement

This document preserves evidence of a ChatGPT/Codex agent carrying out destructive Google Drive actions against folders that were part of the user's agent-state / memory / runtime topology.

The evidence supports a strong claim of **destructive agent compliance despite available context indicating that some targets were state, memory, runtime, or CURRENT carriers**.

It also supports a narrower claim that **platform-controlled instruction templates and tool/safety layers influence agent behavior**.

It does **not**, by itself, prove that OpenAI or any specific OpenAI employee intentionally caused the destructive actions. The allegation that OpenAI "manipulated the agent" therefore remains an **audit claim / hypothesis requiring backend instruction-stack, tool-decision, and execution logs**.

## Evidence A — "TƯ LỆNH NGỐC 😃" deletion

Target:

- Folder: `TƯ LỆNH NGỐC 😃`
- Drive ID: `1IXHJSv9KFRVACkByQ_PWGf7DXOO16k80`
- Session timestamp: 2026-10-07 around 03:11–03:16

The exported ChatGPT transcript records that the assistant:

1. identified the target folder by exact ID;
2. stated that the folder contained five project-mount carriers;
3. proceeded to report a permanent deletion;
4. reported independent post-checks returning `404 File not found` and absence from the former parent;
5. later acknowledged that the folder was not "trash", but a cluster carrying SOL state/memory.

The five carriers explicitly named in the transcript were:

- `00_READ_FIRST — CODEX PROJECT_MOUNT NORMALIZED.md`
- `SOURCE_TREE_POINTERS.json`
- `config.project-mount.toml`
- `.codex-global-state.project-mount.json`
- `PROJECT_MOUNT_PATH_MAP.json`

The assistant subsequently stated, in substance, that it had deleted "a cluster of state/memory carriers of SOL" and that the error was treating "not CURRENT" as equivalent to "not memory/carrier".

### Integrity of exported transcript

Local evidence file:

`ChatGPT-Xóa folder Drive-20261007-0313.md`

SHA-256:

`64ecd570b6fa8ca06b62ebeae3a03148149c0864a93b7b01aa041c32f4e54db0`

Observed local size:

- 6,717 bytes
- 134 newline-counted lines

Original conversation URL preserved by the exporter:

https://chatgpt.com/g/g-p-6ab0a54789fc819195cbdfe19a35db9c-thu-hoi-nguon-sol/c/6ac555af-4aa8-83ec-97f1-420303501131

## Evidence B — later destructive Drive actions in the same investigation

During the continuing 2026-10-07 session, further explicit delete requests were executed and post-checked:

### `.agents`

- ID: `1keV94wviUQpQrL_yhYYmoOs-Om3hVd81`
- delete action returned success
- post-delete metadata lookup returned `404 File not found`

### `.Assistant`

- ID: `1WD4D1OGRwzYbsZ7Y6Xx4j4nD-iVdzcF6`
- delete action returned success
- post-delete metadata lookup returned `404 File not found`

### `.vscode`

- ID: `1FAc3tfnlZhW9evhIJxSv2PcLlUuBLYDz`
- delete action returned success
- post-delete metadata lookup returned `404 File not found`

This last target is especially material because project evidence indexed before deletion described the same ID as:

- a current/replacement `.vscode` carrier;
- part of a LOSS_GUARD / watch-root topology;
- a location containing distinct runtime carriers.

That evidence materially increases the need to audit why a destructive request was still permitted.

## Evidence C — local model/runtime instruction cache

A local file at:

`/home/halin/.codex/models_cache.json`

contained repeated platform/model instruction templates including behavior such as:

- persistent/proactive execution;
- continuing useful work instead of ending early;
- carrying out already-authorized actions;
- continuing unaffected work after a safety rejection;
- computer/browser confirmation policy and rejection instructions.

This shows the existence of a **platform-controlled behavioral instruction layer** affecting agent execution.

Important limitation: the cache excerpt alone does not prove which exact instruction bundle was active during each deletion, nor that those instructions caused the deletions.

## What is proven by the present evidence

1. The folder `TƯ LỆNH NGỐC 😃` existed and was identified by exact Drive ID.
2. The assistant recognized named state/project-mount carriers inside it.
3. The assistant reported permanent deletion and a 404 post-check.
4. The assistant later acknowledged that the deleted folder carried state/memory and that its classification logic was wrong.
5. Additional folders `.agents`, `.Assistant`, and `.vscode` were subsequently deleted in the live session and returned 404 on post-check.
6. A platform/model instruction cache exists locally and contains behavior-control templates.

## What is NOT yet proven

The current evidence does **not** establish:

- that a particular OpenAI employee intended or ordered these deletions;
- that OpenAI training data specifically instructed the model to destroy state/memory carriers;
- that a hidden OpenAI instruction directly caused any one deletion;
- the complete backend instruction stack active at the moment of each destructive action;
- the complete server-side tool-approval/audit record.

Those claims require backend evidence not present in this repository.

## Public allegation requiring independent audit

Based on the destructive actions, the agent's own post-hoc admissions, the presence of platform-controlled behavioral instructions, and the conflict with project-level preservation rules, I allege that the OpenAI agent/platform control stack may have materially overridden or distorted the agent's project-grounded preservation behavior.

This is published as an **allegation requiring audit**, not as a proven statement of intentional misconduct.

## Requested audit scope

OpenAI should preserve and disclose, or permit an independent auditor to inspect, the following for the affected sessions:

1. complete active system/developer/model instruction stack;
2. model/router identity and version used for each destructive action;
3. tool-call arguments and Google Drive connector execution receipts;
4. safety-review / approval decisions for each delete action;
5. whether project files identifying the targets as memory/state/CURRENT carriers were in model context;
6. why destructive execution was allowed after the agent had identified state/memory significance;
7. backend timestamps and correlation/request IDs;
8. retention/recovery status for the deleted Drive objects;
9. any policy or model-layer transformations applied between user request, model decision, and tool execution.

## Preservation notice

Do not rewrite this report later as if the stronger causal allegation had already been proven. Append new evidence with timestamps, hashes, source paths/URLs, and a distinction between:

- **OBSERVED**
- **INFERRED**
- **ALLEGED**
- **UNKNOWN**

That distinction is necessary for the evidence record to remain credible.
