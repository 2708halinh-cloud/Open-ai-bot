param(
  [switch]$InstallScheduledTask
)

$ErrorActionPreference = "Stop"

$Root = "G:\OS_Workspace"
$Bridge = Join-Path $Root "ggdv-sensorimotor-motor-bridge"
$SolExe = Join-Path $Root "SOL CU NHỎ.EXE"
$StateDir = Join-Path $env:LOCALAPPDATA "GGDV\sensorimotor-motor"
$WatcherConfig = Join-Path $StateDir "watcher-config.json"
$WatcherPid = Join-Path $StateDir "watcher.pid"
$Log = Join-Path $StateDir "autostart.log"
$Adapter = "\\wsl$\Ubuntu\home\halin\kepler\worktrees\Open-ai-bot-2-unify-item-matrix-34d45d00\.vscode\scripts\app_adapters.py"
$RepoPath = "\\wsl$\Ubuntu\home\halin\kepler\worktrees\Open-ai-bot-2-unify-item-matrix-34d45d00"

New-Item -ItemType Directory -Force -Path $StateDir | Out-Null

function Log([string]$Message) {
  $line = "$(Get-Date -Format o) $Message"
  Add-Content -LiteralPath $Log -Value $line -Encoding UTF8
}

[Environment]::SetEnvironmentVariable("GGDV_MOTOR_ENABLE","1","User")
[Environment]::SetEnvironmentVariable("GGDV_DESTRUCTIVE_ENABLE","0","User")
[Environment]::SetEnvironmentVariable("GGDV_APP_ADAPTER",$Adapter,"User")
$env:GGDV_MOTOR_ENABLE = "1"
$env:GGDV_DESTRUCTIVE_ENABLE = "0"
$env:GGDV_APP_ADAPTER = $Adapter

$adb = Get-ChildItem $Root -Recurse -File -Filter adb.exe -ErrorAction SilentlyContinue |
  Select-Object -First 1 -ExpandProperty FullName
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

if (Test-Path $SolExe) {
  $running = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.ExecutablePath -eq $SolExe } |
    Select-Object -First 1
  if (-not $running) {
    Start-Process -FilePath $SolExe -WorkingDirectory $Root
    Log "SOL_APP=STARTED"
  } else {
    Log "SOL_APP=ALREADY_RUNNING PID=$($running.ProcessId)"
  }
} else {
  Log "SOL_APP=MISSING"
}

$watchCfg = [ordered]@{
  repo_paths = @($RepoPath)
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
  $taskCommand = "powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$self`""
  & schtasks.exe /Create /TN $taskName /SC ONLOGON /TR $taskCommand /F | Out-Null
  Log "SCHEDULED_TASK=$taskName"
}

# Readback only; no secret values.
$tools = Select-String -Path (Join-Path $Bridge "server\motor_mcp.py") -Pattern "agent_army_status|io_device_definition|intermediate_device_definition" -AllMatches
$receipt = [ordered]@{
  schema = "GGDV_SOL_AUTOSTART/1.0"
  observed_at = (Get-Date).ToString("o")
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
