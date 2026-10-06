param(
  [string]$Distro = 'Ubuntu',
  [string]$WslRoot = $env:GGDV_WSL_REPO_ROOT
)
$ErrorActionPreference = 'Stop'

function Find-GgdvWslRoot {
  param([string]$DistroName)
  $discover = @'
for d in "$HOME"/kepler/worktrees/*; do
  [ -e "$d/.git" ] || continue
  u="$(git -C "$d" remote get-url origin 2>/dev/null || true)"
  case "$u" in
    *2708halinh-cloud/Open-ai-bot*) printf '%s\n' "$d"; exit 0 ;;
  esac
done
exit 1
'@
  $candidate = (& wsl.exe -d $DistroName -- bash -lc $discover 2>$null | Select-Object -First 1)
  if ($candidate) { return $candidate.Trim() }
  return $null
}

if ([string]::IsNullOrWhiteSpace($WslRoot)) {
  $WslRoot = Find-GgdvWslRoot -DistroName $Distro
}

if ([string]::IsNullOrWhiteSpace($WslRoot)) {
  $scriptPath = (Resolve-Path -LiteralPath $MyInvocation.MyCommand.Path).Path
  if ($scriptPath -match '^\\\\wsl\$\\([^\\]+)\\(.+)$') {
    $Distro = $Matches[1]
    $linuxPath = '/' + ($Matches[2] -replace '\\','/')
    $suffix = '/LOCAL_BRIDGE/bootstrap_once.ps1'
    if (-not $linuxPath.EndsWith($suffix)) { throw "Cannot derive repository root from $scriptPath" }
    $WslRoot = $linuxPath.Substring(0, $linuxPath.Length - $suffix.Length)
  } else {
    $repoWin = Split-Path -Parent (Split-Path -Parent $scriptPath)
    $converted = (& wsl.exe -d $Distro -- wslpath -a $repoWin 2>$null | Select-Object -First 1)
    if ($converted) { $WslRoot = $converted.Trim() }
  }
}

if ([string]::IsNullOrWhiteSpace($WslRoot)) {
  throw 'Unable to resolve Open-ai-bot WSL worktree. Set GGDV_WSL_REPO_ROOT or pass -WslRoot.'
}

$identity=[Security.Principal.WindowsIdentity]::GetCurrent()
$principal=New-Object Security.Principal.WindowsPrincipal($identity)
if(-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){
  $elevatedArgs = @(
    '-NoProfile','-ExecutionPolicy','Bypass',
    '-File', $MyInvocation.MyCommand.Path,
    '-Distro', $Distro,
    '-WslRoot', $WslRoot
  )
  Start-Process powershell.exe -Verb RunAs -ArgumentList $elevatedArgs
  exit
}

$TaskName='TESSERACT_LOCAL_BRIDGE'
$bashScript = @'
root=''
for d in "$HOME"/kepler/worktrees/*; do
  [ -e "$d/.git" ] || continue
  u="$(git -C "$d" remote get-url origin 2>/dev/null || true)"
  case "$u" in
    *2708halinh-cloud/Open-ai-bot*) root="$d"; break ;;
  esac
done
if [ -z "$root" ]; then root='__FALLBACK_ROOT__'; fi
cd "$root" && exec python3 LOCAL_BRIDGE/bridge.py
'@
$bashScript = $bashScript.Replace('__FALLBACK_ROOT__', $WslRoot)
$encoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($bashScript))
$arg="-d $Distro -- bash -lc `"echo '$encoded' | base64 -d | bash`""
$action=New-ScheduledTaskAction -Execute 'wsl.exe' -Argument $arg
$trigger=New-ScheduledTaskTrigger -AtLogOn
$settings=New-ScheduledTaskSettingsSet -StartWhenAvailable -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1)
$principalSpec=New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principalSpec -Force | Out-Null
Start-ScheduledTask -TaskName $TaskName
Write-Host "TESSERACT_LOCAL_BRIDGE_STARTED root=$WslRoot"
