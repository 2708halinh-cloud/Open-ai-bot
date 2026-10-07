#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODEL_ZIP="$(ls -1t "$ROOT"/BUILD/sol-long-mach-model-*.zip | head -n1)"
MODEL_HOME="${XDG_DATA_HOME:-$HOME/.local/share}/sol-long-mach/model/d9feca36"
mkdir -p "$MODEL_HOME"
if [ ! -f "$MODEL_HOME/AGENTS.md" ]; then
  python3 - "$MODEL_ZIP" "$MODEL_HOME" <<'PY'
import sys, zipfile
with zipfile.ZipFile(sys.argv[1]) as z: z.extractall(sys.argv[2])
PY
fi
APPDIR="$ROOT/INSTALLERS/linux"
APPIMAGE="$(find "$APPDIR" -maxdepth 2 -type f -name '*.AppImage' | head -n1 || true)"
DEB="$(find "$APPDIR" -maxdepth 2 -type f -name '*.deb' | head -n1 || true)"
if [ -n "$APPIMAGE" ]; then
  mkdir -p "$HOME/.local/bin"; cp "$APPIMAGE" "$HOME/.local/bin/tesseract-desktop"; chmod +x "$HOME/.local/bin/tesseract-desktop"
  echo "APP_ACTION=APPIMAGE_INSTALLED"
elif [ -n "$DEB" ] && command -v sudo >/dev/null 2>&1; then
  sudo dpkg -i "$DEB" || sudo apt-get -f install -y
  echo "APP_ACTION=DEB_INSTALLED"
else
  echo "APP_ACTION=NO_NATIVE_INSTALLER_FOUND"
fi
echo "MODEL_HOME=$MODEL_HOME"
