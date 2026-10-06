#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
BOOT_ENV="$REPO_ROOT/.runtime/TESSERACT_BOOT_G.env"
CONTROLLER_WSL="$REPO_ROOT/terminal/tesseract_boot_controller.ps1"
RECEIPT_WSL="$REPO_ROOT/.runtime/BOOT_RECEIPT_G.json"

[[ -f "$BOOT_ENV" ]] || { echo "missing $BOOT_ENV" >&2; exit 1; }
[[ -f "$CONTROLLER_WSL" ]] || { echo "missing $CONTROLLER_WSL" >&2; exit 1; }
set -a
# shellcheck disable=SC1090
source "$BOOT_ENV"
set +a

[[ "${TESSERACT_BOOT_MODE:-}" == "ROOT_NEUTRAL_USB" ]] || { echo "TESSERACT_BOOT_MODE must be ROOT_NEUTRAL_USB" >&2; exit 1; }
command -v powershell.exe >/dev/null 2>&1 || { echo "powershell.exe unavailable from WSL" >&2; exit 1; }
command -v wslpath >/dev/null 2>&1 || { echo "wslpath unavailable" >&2; exit 1; }

find_image() {
  local candidates=()
  [[ -n "${TESSERACT_BOOT_IMAGE:-}" ]] && candidates+=("$TESSERACT_BOOT_IMAGE")
  candidates+=(
    "$REPO_ROOT/$TESSERACT_BOOT_IMAGE_NAME"
    "$REPO_ROOT/dist/$TESSERACT_BOOT_IMAGE_NAME"
    "$HOME/Downloads/$TESSERACT_BOOT_IMAGE_NAME"
  )
  shopt -s nullglob
  local u
  for u in /mnt/c/Users/*; do
    candidates+=(
      "$u/Downloads/$TESSERACT_BOOT_IMAGE_NAME"
      "$u/Desktop/$TESSERACT_BOOT_IMAGE_NAME"
      "$u/OneDrive/Downloads/$TESSERACT_BOOT_IMAGE_NAME"
    )
  done
  shopt -u nullglob
  local p
  for p in "${candidates[@]}"; do
    if [[ -f "$p" ]]; then printf "%s\n" "$p"; return 0; fi
  done
  return 1
}

IMAGE_WSL="$(find_image || true)"
[[ -n "$IMAGE_WSL" && -f "$IMAGE_WSL" ]] || { echo "boot image not found: $TESSERACT_BOOT_IMAGE_NAME" >&2; exit 2; }
ACTUAL_SHA="$(sha256sum "$IMAGE_WSL" | awk '{print $1}')"
[[ "$ACTUAL_SHA" == "$TESSERACT_BOOT_IMAGE_SHA256" ]] || { echo "SHA256 mismatch: $ACTUAL_SHA" >&2; exit 3; }
ACTUAL_SIZE="$(stat -c "%s" "$IMAGE_WSL")"
[[ "$ACTUAL_SIZE" == "$TESSERACT_BOOT_IMAGE_SIZE" ]] || { echo "size mismatch: $ACTUAL_SIZE" >&2; exit 4; }

IDENTITY_SPEC="${TESSERACT_BOOT_TARGET_IDENTITY_FILE:-.runtime/TESSERACT_BOOT_TARGET_IDENTITY.json}"
if [[ "$IDENTITY_SPEC" = /* ]]; then
  IDENTITY_WSL="$IDENTITY_SPEC"
else
  IDENTITY_WSL="$REPO_ROOT/$IDENTITY_SPEC"
fi
mkdir -p "$(dirname "$IDENTITY_WSL")" "$(dirname "$RECEIPT_WSL")"

IMAGE_WIN="$(wslpath -w "$IMAGE_WSL")"
IDENTITY_WIN="$(wslpath -w "$IDENTITY_WSL")"
RECEIPT_WIN="$(wslpath -w "$RECEIPT_WSL")"
CONTROLLER_WIN="$(wslpath -w "$CONTROLLER_WSL")"

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$CONTROLLER_WIN" \
  -ImagePath "$IMAGE_WIN" \
  -ExpectedSha256 "$TESSERACT_BOOT_IMAGE_SHA256" \
  -ExpectedSize "$TESSERACT_BOOT_IMAGE_SIZE" \
  -ReceiptPath "$RECEIPT_WIN" \
  -IdentityPath "$IDENTITY_WIN" \
  -PreferredDriveLetter "${TESSERACT_BOOT_PREFERRED_DRIVE:-G}" \
  -AllowIdentityBootstrap "${TESSERACT_BOOT_ALLOW_IDENTITY_BOOTSTRAP:-TRUE}" \
  -RequireUsb "${TESSERACT_BOOT_REQUIRE_USB:-TRUE}" \
  -ForbidSystemDisk "${TESSERACT_BOOT_FORBID_SYSTEM_DISK:-TRUE}" \
  -RebootToFirmware "${TESSERACT_BOOT_REBOOT_TO_FIRMWARE:-TRUE}"
