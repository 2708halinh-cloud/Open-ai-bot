# SOL MODEL STUDIO

Local-first model cockpit for **X-TIME · GGDV HUMAN 1.0** and **GGDV HUMAN SOL**.

## Run from VS Code / terminal

Windows Node 26 is already available on this workstation.

```powershell
node "\\wsl$\Ubuntu\home\halin\kepler\worktrees\Open-ai-bot-2-unify-item-matrix-34d45d00\SOL_MODEL_STUDIO\server.mjs"
```

Then open:

```
http://127.0.0.1:4789
```

Or use the VS Code task in `.vscode/tasks.json`.

## Presets

- **GGDV HUMAN SOL 1.0** → Ollama `ggdv-human-sol:1.0` · ctx 16384 · temp 0.65
- **X-TIME · GGDV HUMAN 1.0** → Ollama `x-time-ggdv-human:1.0` · ctx 32768 · temp 0.35
- **GGDV HUMAN SOL CODER** → Ollama `ggdv-human-sol-coder:1.0` · ctx 32768 · temp 0.2
- **LM Studio / OpenAI-compatible** → default endpoint `http://127.0.0.1:1234/v1`
- **Hermes / OpenAI-compatible** → default endpoint `http://127.0.0.1:8080/v1`

The server binds to `127.0.0.1` only. Remote model endpoints are blocked unless
`SOL_ALLOW_REMOTE_ENDPOINTS=1` is explicitly set.

## LM Studio direct GGUF

Materialized local exports:

```
D:\AI_LOCAL\SOL_MODEL_EXPORTS\Gemma4-8B-Q4_K_M-GGDV-base.gguf
D:\AI_LOCAL\SOL_MODEL_EXPORTS\Qwen2.5-Coder-7.6B-Q4_K_M-GGDV.gguf
```

These are **hardlinks** to the existing Ollama model blobs, not duplicate 9.6/4.68 GB copies.

The X-TIME and GGDV HUMAN SOL variants share the same Gemma 4 GGUF base and differ by
Modelfile system prompt + generation parameters. Their exact observed Modelfiles are stored
beside the GGUF exports.

## Model provenance

Observed from live Ollama:

- `x-time-ggdv-human:1.0` → Gemma 4, Q4_K_M, Apache-2.0
- `ggdv-human-sol:1.0` → same Gemma 4 GGUF base, Apache-2.0
- `ggdv-human-sol-coder:1.0` → Qwen2.5 Coder 7.6B Q4_K_M base blob, Apache-2.0 as reported by Ollama model metadata

These are runtime configurations/personas over base weights; do not describe them as new fine-tuned weights unless a later source proves that.

## Privacy

API keys are not persisted by the browser UI. Chat/session config is kept in localStorage.
The Node proxy blocks non-loopback model endpoints by default.
