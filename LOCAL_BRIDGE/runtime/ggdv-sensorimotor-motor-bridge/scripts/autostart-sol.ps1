param(
  [switch]$InstallScheduledTask,
  [string]$Root,
  [string]$RepoPath,
  [string]$Adapter,
  [string]$Distro = 'Ubuntu'
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) { $Root = $env:GGDV_OS_WORKSPACE_ROOT }
if ([string]::IsNullOrWhiteSpace($Root)) { $Root = "G:\OS_Workspace" }

$Bridge = Join-Path $Root "ggdv-sensorimotor-motor-bridge"
$SolExe = Join-Path $Root "SOL CU NHỎ.EXE"
$StateDir = Join-Path $Root "TESSERACT_OS\runtime\state"
$WatcherConfig = Join-Path $StateDir "watcher-config.json"
$WatcherPid = Join-Path $StateDir "watcher.pid"
$Log = Join-Path $StateDir "autostart.log"

New-Item -ItemType Directory -Force -Path $StateDir | Out-Null

function Log([string]$Message) {
  $line = "$(Get-Date -Format o) $Message"
  Add-Content -LiteralPath $Log -Value $line -Encoding UTF8
}

function Resolve-RepoPath([string]$ExplicitPath) {
  if (-not [string]::IsNullOrWhiteSpace($ExplicitPath)) { return $ExplicitPath }
  if (-not [string]::IsNullOrWhiteSpace($env:GGDV_REPO_PATH)) { return $env:GGDV_REPO_PATH }

  $wsl = Get-Command wsl.exe -ErrorAction SilentlyContinue
  if (-not $wsl) { return $null }

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
  $linuxRepo = (& $wsl.Source -d $Distro -- bash -lc $discover 2>$null | Select-Object -First 1)
  if (-not $linuxRepo) { return $null }
  $linuxRepo = $linuxRepo.Trim()
  return ('\\wsl$\' + $Distro + ($linuxRepo -replace '/', '\'))
}

$RepoPath = Resolve-RepoPath $RepoPath
if ([string]::IsNullOrWhiteSpace($Adapter)) { $Adapter = $env:GGDV_APP_ADAPTER }
if ([string]::IsNullOrWhiteSpace($Adapter) -and -not [string]::IsNullOrWhiteSpace($RepoPath)) {
  $candidateAdapter = Join-Path $RepoPath ".vscode\scripts\app_adapters.py"
  if (Test-Path -LiteralPath $candidateAdapter) { $Adapter = $candidateAdapter }
}

[Environment]::SetEnvironmentVariable("GGDV_MOTOR_ENABLE","1","User")
[Environment]::SetEnvironmentVariable("GGDV_DESTRUCTIVE_ENABLE","0","User")
[Environment]::SetEnvironmentVariable("GGDV_SENSORIMOTOR_STATE_DIR",$StateDir,"User")
$env:GGDV_MOTOR_ENABLE = "1"
$env:GGDV_DESTRUCTIVE_ENABLE = "0"
$env:GGDV_SENSORIMOTOR_STATE_DIR = $StateDir

if (-not [string]::IsNullOrWhiteSpace($RepoPath)) {
  [Environment]::SetEnvironmentVariable("GGDV_REPO_PATH",$RepoPath,"User")
  $env:GGDV_REPO_PATH = $RepoPath
  Log "REPO_PATH=$RepoPath"
} else {
  Log "REPO_PATH=NOT_RESOLVED"
}

if (-not [string]::IsNullOrWhiteSpace($Adapter)) {
  [Environment]::SetEnvironmentVariable("GGDV_APP_ADAPTER",$Adapter,"User")
  $env:GGDV_APP_ADAPTER = $Adapter
  Log "APP_ADAPTER=$Adapter"
} else {
  Log "APP_ADAPTER=NOT_RESOLVED"
}

$adb = $null
if (-not [string]::IsNullOrWhiteSpace($env:GGDV_ADB_PATH) -and (Test-Path -LiteralPath $env:GGDV_ADB_PATH -PathType Leaf)) {
  $adb = $env:GGDV_ADB_PATH
}
if (-not $adb) {
  $userAdb = Join-Path $env:USERPROFILE "platform-tools-latest-windows\platform-tools\adb.exe"
  if (Test-Path -LiteralPath $userAdb -PathType Leaf) { $adb = $userAdb }
}
if (-not $adb) {
  $adb = Get-ChildItem $Root -Recurse -File -Filter adb.exe -ErrorAction SilentlyContinue |
    Select-Object -First 1 -ExpandProperty FullName
}
if ($adb) {
  [Environment]::SetEnvironmentVariable("GGDV_ADB_PATH",$adb,"User")
  $env:GGDV_ADB_PATH = $adb
  Log "ADB=$adb"
} else {
  Log "ADB=NOT_FOUND"
}

if (-not (Test-Path $Bridge)) { throw "Bridge missing: $Bridge" }
if (-not (Test-Path (Join-Path $Bridge "server\motor_mcp.py"))) { throw "motor_mcp.py missing" }

$plugin = Get-Content (Join-Path $Bridge "plugin.json") -Raw | ConvertFrom-Json
Log "BRIDGE_VERSION=$($plugin.version)"

if (Test-Path -LiteralPath $SolExe -PathType Leaf) {
  $running = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.ExecutablePath -eq $SolExe } |
    Select-Object -First 1
  if (-not $running) {
    Start-Process -FilePath $SolExe -WorkingDirectory $Root
    Log "SOL_APP=STARTED"
  } else {
    Log "SOL_APP=ALREADY_RUNNING PID=$($running.ProcessId)"
  }
} elseif (Test-Path -LiteralPath $SolExe -PathType Container) {
  Log "SOL_APP=FOLDER_NOT_EXECUTABLE"
} else {
  Log "SOL_APP=MISSING"
}

$repoPaths = @()
if (-not [string]::IsNullOrWhiteSpace($RepoPath)) { $repoPaths = @($RepoPath) }
$watchCfg = [ordered]@{
  repo_paths = $repoPaths
  adb = [bool]$adb
  poll_seconds = 3
}
$watchCfg | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $WatcherConfig -Encoding UTF8

$watcherAlive = $false
if (Test-Path $WatcherPid) {
  try {
    $pidValue = [int](Get-Content $WatcherPid -Raw).Trim()
    $watcherAlive = [bool](Get-Process -Id $pidValue -ErrorAction SilentlyContinue)
  } catch { $watcherAlive = $false }
}

if (-not $watcherAlive) {
  $py = (Get-Command python -ErrorAction Stop).Source
  $watcher = Join-Path $Bridge "server\watcher.py"
  Start-Process -FilePath $py -ArgumentList @($watcher,"--config",$WatcherConfig) -WorkingDirectory (Split-Path $watcher -Parent) -WindowStyle Hidden
  Start-Sleep -Seconds 2
  Log "WATCHER=START_REQUESTED"
} else {
  Log "WATCHER=ALREADY_RUNNING"
}

if ($InstallScheduledTask) {
  $taskName = "GGDV_SOL_AUTOSTART"
  $self = $MyInvocation.MyCommand.Path
  $taskCommand = "powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$self`" -Root `"$Root`""
  & schtasks.exe /Create /TN $taskName /SC ONLOGON /TR $taskCommand /F | Out-Null
  Log "SCHEDULED_TASK=$taskName"
}

$tools = Select-String -Path (Join-Path $Bridge "server\motor_mcp.py") -Pattern "agent_army_status|io_device_definition|intermediate_device_definition" -AllMatches
$receipt = [ordered]@{
  schema = "GGDV_SOL_AUTOSTART/1.1"
  observed_at = (Get-Date).ToString("o")
  root = $Root
  repo_path = $RepoPath
  bridge = $Bridge
  bridge_version = $plugin.version
  motor_enabled = $env:GGDV_MOTOR_ENABLE
  destructive_enabled = $env:GGDV_DESTRUCTIVE_ENABLE
  app_adapter = $env:GGDV_APP_ADAPTER
  adb_present = [bool]$adb
  watcher_pid_file = $WatcherPid
  watcher_alive = (Test-Path $WatcherPid)
  required_tools_present = (($tools.Matches.Count) -ge 3)
  scheduled_task_requested = [bool]$InstallScheduledTask
}
$receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $StateDir "AUTOSTART_READBACK_CURRENT.json") -Encoding UTF8
$receipt | ConvertTo-Json -Depth 8
