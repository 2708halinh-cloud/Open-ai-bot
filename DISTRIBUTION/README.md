# SOL LONG MẠCH — LOCAL MATERIALIZATION

Canonical source is GitHub. D:\SOL_LONG_MACH is the current local materialized carrier/install cache, not a GGDV/Drive storage root.

## Tree
- MODEL\SOL_RUNTIME — exact clean export of SOL runtime/model source HEAD.
- APP\x-time-web\TESSERACT_DESKTOP — native Tauri application source.
- BUILD — reproducible package/build scripts and model archive.
- INSTALLERS — platform installer payloads + bootstrap scripts.
- RECEIPTS — hashes/build/install readback.

## Canonical source refs
- SOL runtime/model: 2708halinh-cloud/SOL-LONG-MACH, branch sol-long-mach-current, commit d9feca36db44d50f0d9d2b0ce0166231bdfeca45.
- Native app: 2708halinh-cloud/x-time-web, branch tesseract-desktop-mvp-20261006, commit 5ec6f93dc11856bd5609b51026fbe57f4f165495.
- Model package SHA256: c9ac7eb07c816e93f6f35e562dc7749c8fe084edad7b02defeceec64cc8fbdbe.

## Storage boundary
Raw secrets/tokens/credentials are never copied into GitHub/public packages. Runtime resolves secrets from permitted local carriers. Drive/GGDV source IDs remain pointers/provenance only; this local distribution does not use GGDV as package storage.

## Windows
After the native build places a MSI/EXE under INSTALLERS\windows, run:
powershell -ExecutionPolicy Bypass -File INSTALLERS\install-windows.ps1

## Linux/macOS/TESSERACT_OS
Use the matching script in INSTALLERS after placing the native artifact from the TESSERACT Desktop CI/build into the matching platform folder.

