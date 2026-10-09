#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

command -v cargo >/dev/null || { echo "cargo missing"; exit 2; }
command -v npm >/dev/null || { echo "npm missing"; exit 2; }

npm install
npm run tauri build

mkdir -p dist/tesseract-os
BUNDLE_ROOT="src-tauri/target/release/bundle"
[ -d "$BUNDLE_ROOT" ] || { echo "bundle directory missing: $BUNDLE_ROOT" >&2; exit 3; }

mapfile -t bundle_files < <(find "$BUNDLE_ROOT" -maxdepth 4 -type f -print)
[ "${#bundle_files[@]}" -gt 0 ] || { echo "no installer bundle files produced" >&2; exit 4; }

for artifact in "${bundle_files[@]}"; do
  cp -f "$artifact" dist/tesseract-os/
done

artifact_count="$(find dist/tesseract-os -maxdepth 1 -type f ! -name BUILD_RECEIPT.json | wc -l | tr -d ' ')"
[ "$artifact_count" -gt 0 ] || { echo "bundle staging produced no artifacts" >&2; exit 5; }

printf '{"schema":"TESSERACT_DESKTOP_TESSERACT_OS_BUILD/1.1","state":"BUNDLE_STAGED","artifact_count":%s,"host_preserved":true}\n' "$artifact_count" > dist/tesseract-os/BUILD_RECEIPT.json
echo "TESSERACT_OS staged $artifact_count bundle artifact(s) under TESSERACT_DESKTOP/dist/tesseract-os"
