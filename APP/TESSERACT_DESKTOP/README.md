# TESSERACT Desktop

Native local-first agent workspace inspired by the product requirements supplied for Kilo Desktop, but implemented as an independent TESSERACT/UBUBU surface.

## Product surface

- Multi-folder local workspaces.
- Workspace-scoped chat agent.
- Interactive Python cell runner beside chat.
- Workspace-scoped terminal.
- Git status review using the system Git binary.
- Embedded web pane.
- Conda integration gate.
- Provider abstraction for local or hosted OpenAI-compatible model endpoints.
- Local GGUF support through an external OpenAI-compatible local model server.
- Durable first-run enrollment state.

## First-run enrollment

The first launch is blocked behind a review gate for four canonical sources:

1. R-000 — Drive ID `1D9OwoqTIxqg3iCmCi8htsSWpES0yRHOvfC4c4vpCkNE`
2. 0000_TUYÊN NGÔN — Drive ID `1BhNtbSFoH_hx-TyBmTpjZ8PKpeR2rVkY19lXwBBMGIc`
3. 0000_THE_MASTER_TEACHER — Drive ID `1z12kJsMv-qHzHe1Tz60rlR-2122n65Rah0qXzfe_T5k`
4. 152 ITEM — `2708halinh-cloud/Open-ai/item_matrix/152_ITEM_CURRENT.md`, Drive source `1JxkfCpiI7diBPSmTs--NBBz3-kPsnPN-`

The source files are not rewritten. Completion persists only the reviewed source IDs in the app-local `CURRENT_STATE.json`.

## System requirements

Supported release targets:

- macOS Apple Silicon.
- Windows x64.
- Linux x64.
- TESSERACT_OS x64.

Optional host dependencies:

- Git: required for Git integration.
- Python: required for notebook cells.
- Conda: app-managed/runtime integration; account gate is enforced by the app state.
- GGUF: user-provided model file, served through an OpenAI-compatible local server.

## Development

```bash
cd TESSERACT_DESKTOP
npm install
npm run tauri dev
```

Build native installer:

```bash
npm run tauri build
```

## Provider model

Provider configuration stores only:

- provider kind;
- base URL;
- model ID;
- the **name** of the environment variable holding an API key.

Secret values are never persisted by this app.

## Kilo/X-TiMe session trust

Kilo-gated features accept only the signed receipt envelope `XTIME_KILO_SESSION_RECEIPT/2.0`. The envelope contains a base64 payload and an Ed25519 signature; the signed payload must bind `issuer=KILO_XTIME`, the expected account reference, an authenticated session ID, and a future expiry.

The verifier public key is a build-time trust anchor named `XTIME_KILO_RECEIPT_ED25519_PUBLIC_KEY_B64`. CI reads it from the GitHub Actions variable of the same name. Runtime process flags and a locally editable JSON file cannot establish trust by themselves. If the real issuer public key has not been provisioned at build time, the Kilo gate fails closed with `KILO_TRUSTED_ISSUER_KEY_NOT_CONFIGURED_AT_BUILD`.

The issuer-side signing adapter is still an external dependency: this repository deliberately does not invent or commit a private signing key.
