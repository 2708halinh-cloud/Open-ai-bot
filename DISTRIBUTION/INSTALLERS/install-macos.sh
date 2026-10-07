#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODEL_ZIP="$(ls -1t "$ROOT"/BUILD/sol-long-mach-model-*.zip | head -n1)"
MODEL_HOME="$HOME/Library/Application Support/SOL_LONG_MACH/model/d9feca36"
mkdir -p "$MODEL_HOME"
if [ ! -f "$MODEL_HOME/AGENTS.md" ]; then
  /usr/bin/ditto -x -k "$MODEL_ZIP" "$MODEL_HOME"
fi
DMG="$(find "$ROOT/INSTALLERS/macos" -maxdepth 2 -type f -name '*.dmg' | head -n1 || true)"
if [ -n "$DMG" ]; then
  MOUNT="$(hdiutil attach "$DMG" -nobrowse | tail -n1 | awk '{print $NF}')"
  APP="$(find "$MOUNT" -maxdepth 1 -name '*.app' -type d | head -n1)"
  mkdir -p "$HOME/Applications"
  /usr/bin/ditto "$APP" "$HOME/Applications/$(basename "$APP")"
  hdiutil detach "$MOUNT" >/dev/null
  echo "APP_ACTION=DMG_INSTALLED_USER"
else
  echo "APP_ACTION=NO_DMG_FOUND"
fi
echo "MODEL_HOME=$MODEL_HOME"
