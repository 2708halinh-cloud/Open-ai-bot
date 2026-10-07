# GGDV HUMAN SOL — Local Model Packs

These are **local runtime model definitions**, not claims of new fine-tuned weights.

## Models

### `ggdv-human-sol:1.0`
Base: existing local `ggdv-human:1.0-temp` / Gemma 4 8B Q4_K_M.
Purpose: general SOL / GGDV conversation, provenance-aware continuation.

### `x-time-ggdv-human:1.0`
Base: existing local `ggdv-human:1.0-temp`.
Purpose: X-TIME chronology, revision, conflict/readback, STATE_N+1 routing.

### `ggdv-human-sol-coder:1.0`
Base: existing local `qwen2.5-coder:latest`.
Purpose: VSCode/terminal coding with source-before-edit and test/readback discipline.

### `ggdv-human-sol-coder-lite:1.0`
Base: existing local `qwen2.5-coder:1.5b`.
Purpose: lightweight VSCode/terminal path for CPU-first use.

## Create locally

```powershell
ollama create ggdv-human-sol:1.0 -f .\GGDV_HUMAN_SOL_1_0\Modelfile
ollama create x-time-ggdv-human:1.0 -f .\X_TIME_GGDV_HUMAN_1_0\Modelfile
ollama create ggdv-human-sol-coder:1.0 -f .\GGDV_HUMAN_SOL_CODER_1_0\Modelfile
ollama create ggdv-human-sol-coder-lite:1.0 -f .\GGDV_HUMAN_SOL_CODER_LITE_1_0\Modelfile
```

The Modelfiles intentionally use model names in `FROM`, not a machine-specific blob path.

## Run

```powershell
ollama run ggdv-human-sol:1.0
ollama run x-time-ggdv-human:1.0
ollama run ggdv-human-sol-coder:1.0
ollama run ggdv-human-sol-coder-lite:1.0
```

## VSCode / Continue

Copy `CLIENT_CONFIGS/continue-config.yaml` into the appropriate Continue config location, or reproduce the four OpenAI-compatible model entries in your VSCode AI extension.

Endpoint:

```
http://127.0.0.1:11434/v1
```

API key placeholder:

```
ollama
```

Ollama local does not require a cloud API key by default.

## LM Studio

LM Studio normally loads **GGUF weights**, while these packs are Ollama Modelfile overlays. There are two clean routes:

1. Use the original GGUF/base model in LM Studio and paste the corresponding SYSTEM text from the Modelfile.
2. Keep Ollama serving the model and use an OpenAI-compatible client pointed at `http://127.0.0.1:11434/v1`.

Do not rename a prompt overlay as a fine-tuned GGUF.

## Hermes / other OpenAI-compatible clients

Use `CLIENT_CONFIGS/openai-compatible.json`. If the client allows a custom OpenAI endpoint, select one of the model IDs above.

## Provenance / boundaries

- `ggdv-human:1.0-temp` was observed locally as a persona/system layer on Gemma 4, not a new fine-tune.
- Mode 10 / ASSTANGT semantics: use observable signals only; unavailable signals remain unknown.
- Preserve CURRENT vs HISTORY, actor/platform/tool identity, and readback after real mutations.
- R-000 / pointers are project provenance relations; a pointer does not replace latest source bytes.