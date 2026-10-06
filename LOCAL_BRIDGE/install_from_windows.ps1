param(
  [string]$Distro = 'Ubuntu'
)

$ErrorActionPreference = 'Stop'

function Invoke-Wsl([string]$Script) {
  return (& wsl.exe -d $Distro -- bash -lc $Script 2>&1 | Out-String).Trim()
}

$discover = @'
for d in "$HOME"/kepler/worktrees/* "$HOME"/kepler/repos/Open-ai-bot "$HOME"/kepler/Open-ai-bot "$HOME"/Open-ai-bot; do
  [ -d "$d" ] || continue
  git -C "$d" rev-parse --git-dir >/dev/null 2>&1 || continue
  u="$(git -C "$d" remote get-url origin 2>/dev/null || true)"
  case "$u" in
    *2708halinh-cloud/Open-ai-bot*) printf '%s\n' "$d"; exit 0 ;;
  esac
done
if [ -d "$HOME/kepler" ]; then
  while IFS= read -r d; do
    git -C "$d" rev-parse --git-dir >/dev/null 2>&1 || continue
    u="$(git -C "$d" remote get-url origin 2>/dev/null || true)"
    case "$u" in
      *2708halinh-cloud/Open-ai-bot*) printf '%s\n' "$d"; exit 0 ;;
    esac
  done < <(find "$HOME/kepler" -maxdepth 5 -type d 2>/dev/null)
fi
exit 1
'@

$root = (& wsl.exe -d $Distro -- bash -lc $discover 2>$null | Select-Object -First 1)
if ($root) { $root = $root.Trim() }

if ([string]::IsNullOrWhiteSpace($root)) {
  Write-Host 'Open-ai-bot checkout not found. Creating stable WSL checkout...'
  $clone = @'
set -e
mkdir -p "$HOME/kepler/repos"
target="$HOME/kepler/repos/Open-ai-bot"
if [ ! -d "$target/.git" ]; then
  git clone https://github.com/2708halinh-cloud/Open-ai-bot.git "$target"
fi
printf '%s\n' "$target"
'@
  $root = (& wsl.exe -d $Distro -- bash -lc $clone | Select-Object -Last 1)
  if ($root) { $root = $root.Trim() }
}

if ([string]::IsNullOrWhiteSpace($root)) {
  throw 'Unable to locate or create an Open-ai-bot checkout inside WSL.'
}

Write-Host "WSL repository root: $root"

$pull = Invoke-Wsl "git -C '$root' pull --ff-only"
if ($LASTEXITCODE -ne 0) {
  throw "git pull failed for $root :: $pull"
}
if ($pull) { Write-Host $pull }

$temp = Join-Path $env:TEMP 'ggdv_bootstrap_once.ps1'
$b64 = Invoke-Wsl "base64 -w0 '$root/LOCAL_BRIDGE/bootstrap_once.ps1'"
if ([string]::IsNullOrWhiteSpace($b64)) {
  throw 'Failed to read LOCAL_BRIDGE/bootstrap_once.ps1 from WSL checkout.'
}
[IO.File]::WriteAllBytes($temp, [Convert]::FromBase64String($b64))

Write-Host "Installing TESSERACT_LOCAL_BRIDGE from $root ..."
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $temp -Distro $Distro -WslRoot $root
if ($LASTEXITCODE -ne 0) {
  throw "bootstrap_once.ps1 exited with $LASTEXITCODE"
}

Start-Sleep -Seconds 2
$task = Get-ScheduledTask -TaskName 'TESSERACT_LOCAL_BRIDGE' -ErrorAction Stop
Write-Host "TASK=$($task.TaskName) STATE=$($task.State)"
Write-Host 'HOME_SOL queue is already present on main; the bridge will pull it and publish a readback receipt when processed.'
