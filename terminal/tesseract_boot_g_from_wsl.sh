#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
BOOT_ENV="$REPO_ROOT/.runtime/TESSERACT_BOOT_G.env"
RECEIPT_WSL="$REPO_ROOT/.runtime/BOOT_RECEIPT_G.json"

[[ -f "$BOOT_ENV" ]] || { echo "missing $BOOT_ENV" >&2; exit 1; }
set -a
# shellcheck disable=SC1090
source "$BOOT_ENV"
set +a

[[ "${TESSERACT_BOOT_TARGET:-}" == "G" ]] || { echo "target must be G" >&2; exit 1; }
command -v powershell.exe >/dev/null 2>&1 || { echo "powershell.exe unavailable from WSL" >&2; exit 1; }
command -v wslpath >/dev/null 2>&1 || { echo "wslpath unavailable" >&2; exit 1; }

find_image() {
  local candidates=()
  [[ -n "${TESSERACT_BOOT_IMAGE:-}" ]] && candidates+=("$TESSERACT_BOOT_IMAGE")
  candidates+=(
    "$REPO_ROOT/$TESSERACT_BOOT_IMAGE_NAME"
    "$REPO_ROOT/dist/$TESSERACT_BOOT_IMAGE_NAME"
    "/mnt/c/Users/halin/Downloads/$TESSERACT_BOOT_IMAGE_NAME"
    "/mnt/c/Users/halin/Desktop/$TESSERACT_BOOT_IMAGE_NAME"
    "/mnt/c/Users/halin/OneDrive/Downloads/$TESSERACT_BOOT_IMAGE_NAME"
  )
  local p
  for p in "${candidates[@]}"; do
    if [[ -f "$p" ]]; then printf "%s\n" "$p"; return 0; fi
  done
  find /mnt/c/Users -maxdepth 4 -type f -name "$TESSERACT_BOOT_IMAGE_NAME" 2>/dev/null | head -n1
}

IMAGE_WSL="$(find_image || true)"
[[ -n "$IMAGE_WSL" && -f "$IMAGE_WSL" ]] || { echo "boot image not found: $TESSERACT_BOOT_IMAGE_NAME" >&2; exit 2; }
ACTUAL_SHA="$(sha256sum "$IMAGE_WSL" | awk '{print $1}')"
[[ "$ACTUAL_SHA" == "$TESSERACT_BOOT_IMAGE_SHA256" ]] || { echo "SHA256 mismatch: $ACTUAL_SHA" >&2; exit 3; }
ACTUAL_SIZE="$(stat -c "%s" "$IMAGE_WSL")"
[[ "$ACTUAL_SIZE" == "$TESSERACT_BOOT_IMAGE_SIZE" ]] || { echo "size mismatch: $ACTUAL_SIZE" >&2; exit 4; }

IMAGE_WIN="$(wslpath -w "$IMAGE_WSL")"
RECEIPT_WIN="$(wslpath -w "$RECEIPT_WSL")"
PS1="$(mktemp --suffix=.ps1)"
trap 'rm -f "$PS1"' EXIT

cat > "$PS1" <<'POWERSHELL'
param(
  [Parameter(Mandatory=$true)][string]$ImagePath,
  [Parameter(Mandatory=$true)][string]$ExpectedSha256,
  [Parameter(Mandatory=$true)][Int64]$ExpectedSize,
  [Parameter(Mandatory=$true)][string]$ReceiptPath
)
$ErrorActionPreference = "Stop"
function Fail([string]$Message) { Write-Error $Message; exit 1 }

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
  $self = $MyInvocation.MyCommand.Path
  $args = @("-NoProfile","-ExecutionPolicy","Bypass","-File","`"$self`"","-ImagePath","`"$ImagePath`"","-ExpectedSha256","$ExpectedSha256","-ExpectedSize","$ExpectedSize","-ReceiptPath","`"$ReceiptPath`"")
  $p = Start-Process powershell.exe -Verb RunAs -ArgumentList $args -Wait -PassThru
  exit $p.ExitCode
}

if (-not (Test-Path -LiteralPath $ImagePath)) { Fail "Image not found: $ImagePath" }
$img = Get-Item -LiteralPath $ImagePath
if ($img.Length -ne $ExpectedSize) { Fail "Image size mismatch" }
$sha = (Get-FileHash -Algorithm SHA256 -LiteralPath $ImagePath).Hash.ToLowerInvariant()
if ($sha -ne $ExpectedSha256.ToLowerInvariant()) { Fail "Image SHA256 mismatch" }

$partition = Get-Partition -DriveLetter G -ErrorAction Stop
$disk = Get-Disk -Number $partition.DiskNumber -ErrorAction Stop
if ($disk.IsBoot -or $disk.IsSystem) { Fail "G: maps to Windows boot/system disk" }
if ($disk.IsReadOnly) { Fail "G: target disk is read-only" }
if ($disk.BusType -ne "USB") { Fail "G: is not a USB disk; BusType=$($disk.BusType)" }
if ($disk.Size -lt $img.Length) { Fail "G: USB is smaller than image" }

$diskNumber = [int]$disk.Number
$devicePath = "\\.\PhysicalDrive$diskNumber"
& mountvol.exe G: /p | Out-Null
if ($LASTEXITCODE -ne 0) { Fail "Unable to dismount G:" }
Start-Sleep -Milliseconds 800

$bufferSize = 4MB
$buffer = New-Object byte[] $bufferSize
$imageStream = $null
$diskStream = $null
try {
  $imageStream = [System.IO.File]::Open($ImagePath,[System.IO.FileMode]::Open,[System.IO.FileAccess]::Read,[System.IO.FileShare]::Read)
  $diskStream = New-Object System.IO.FileStream($devicePath,[System.IO.FileMode]::Open,[System.IO.FileAccess]::ReadWrite,[System.IO.FileShare]::ReadWrite,$bufferSize,[System.IO.FileOptions]::WriteThrough)
  $diskStream.Position = 0
  [Int64]$written = 0
  while (($read = $imageStream.Read($buffer,0,$buffer.Length)) -gt 0) {
    $diskStream.Write($buffer,0,$read)
    $written += $read
    $pct = [Math]::Min(100,[Math]::Round(($written * 100.0) / $img.Length,1))
    Write-Progress -Activity "Writing TESSERACT OS to USB G:" -Status "$pct%" -PercentComplete $pct
  }
  $diskStream.Flush($true)
  Write-Progress -Activity "Writing TESSERACT OS to USB G:" -Completed
} finally {
  if ($diskStream) { $diskStream.Dispose() }
  if ($imageStream) { $imageStream.Dispose() }
}

$hash = [System.Security.Cryptography.SHA256]::Create()
$src = $null
try {
  $src = New-Object System.IO.FileStream($devicePath,[System.IO.FileMode]::Open,[System.IO.FileAccess]::Read,[System.IO.FileShare]::ReadWrite,$bufferSize,[System.IO.FileOptions]::SequentialScan)
  [Int64]$remaining = $img.Length
  while ($remaining -gt 0) {
    $want = [int][Math]::Min($buffer.Length,$remaining)
    $read = $src.Read($buffer,0,$want)
    if ($read -le 0) { Fail "Unexpected end of device during readback" }
    [void]$hash.TransformBlock($buffer,0,$read,$null,0)
    $remaining -= $read
  }
  [void]$hash.TransformFinalBlock([byte[]]::new(0),0,0)
  $readbackSha = ([BitConverter]::ToString($hash.Hash)).Replace("-","").ToLowerInvariant()
} finally {
  if ($src) { $src.Dispose() }
  $hash.Dispose()
}
if ($readbackSha -ne $ExpectedSha256.ToLowerInvariant()) { Fail "Raw readback SHA256 mismatch" }

$receipt = [ordered]@{
  schema = "TESSERACT_OS_LOCAL_BOOT_RECEIPT/1.0"
  target_drive = "G:"
  physical_disk = $diskNumber
  usb_name = $disk.FriendlyName
  bus_type = [string]$disk.BusType
  image = $img.Name
  image_size = $img.Length
  image_sha256 = $sha
  readback_sha256 = $readbackSha
  write_verified = $true
  boot_path = "EFI/BOOT/BOOTX64.EFI"
  next_action = "UEFI_FIRMWARE_BOOT"
  timestamp = (Get-Date).ToString("o")
}
$receipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $ReceiptPath -Encoding UTF8
shutdown.exe /r /fw /t 8 /c "TESSERACT OS: boot USB from firmware"
POWERSHELL

PS1_WIN="$(wslpath -w "$PS1")"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$PS1_WIN" -ImagePath "$IMAGE_WIN" -ExpectedSha256 "$TESSERACT_BOOT_IMAGE_SHA256" -ExpectedSize "$TESSERACT_BOOT_IMAGE_SIZE" -ReceiptPath "$RECEIPT_WIN"
