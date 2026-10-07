param(
  [string]$StateDir = ""
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($StateDir)) {
  $StateDir = Join-Path $env:LOCALAPPDATA "GGDV\sensorimotor-motor"
}
New-Item -ItemType Directory -Force -Path $StateDir | Out-Null

$EventLog = Join-Path $StateDir "carrier-events.jsonl"
$PidFile = Join-Path $StateDir "carrier-watch.pid"
Set-Content -LiteralPath $PidFile -Value $PID -Encoding ASCII

$watchers = @{}
$subscriptions = @{}
$recent = @{}

function Emit-CarrierEvent {
  param(
    [string]$Drive,
    [string]$Root,
    [string]$Change,
    [string]$Path = "",
    [string]$OldPath = "",
    [string]$Detail = ""
  )
  $payload = [ordered]@{
    observed_at = (Get-Date).ToUniversalTime().ToString("o")
    kind = "FILESYSTEM_CARRIER_EVENT"
    drive = $Drive
    root = $Root
    change = $Change
    path = $Path
    old_path = $OldPath
    detail = $Detail
  }
  $line = ($payload | ConvertTo-Json -Depth 5 -Compress) + [Environment]::NewLine
  $bytes = [System.Text.Encoding]::UTF8.GetBytes($line)
  $stream = $null
  for ($attempt = 0; $attempt -lt 20; $attempt++) {
    try {
      $stream = [System.IO.File]::Open(
        $EventLog,
        [System.IO.FileMode]::Append,
        [System.IO.FileAccess]::Write,
        [System.IO.FileShare]::ReadWrite
      )
      $stream.Write($bytes, 0, $bytes.Length)
      $stream.Flush()
      return
    } catch {
      if ($attempt -ge 19) { throw }
      Start-Sleep -Milliseconds 50
    } finally {
      if ($stream) {
        try { $stream.Dispose() } catch {}
        $stream = $null
      }
    }
  }
}

function Bind-DriveWatcher {
  param([string]$DriveName, [string]$Root)
  if ($watchers.ContainsKey($Root)) { return }

  try {
    $fsw = New-Object System.IO.FileSystemWatcher
    $fsw.Path = $Root
    $fsw.IncludeSubdirectories = $true
    $fsw.NotifyFilter = [System.IO.NotifyFilters]'FileName, DirectoryName, LastWrite, Size, CreationTime'
    $fsw.InternalBufferSize = 65536
    $fsw.EnableRaisingEvents = $true

    foreach ($evt in @("Created","Deleted","Changed","Renamed","Error")) {
      $sid = "GGDV_CARRIER::$DriveName::$evt"
      Register-ObjectEvent -InputObject $fsw -EventName $evt -SourceIdentifier $sid | Out-Null
      $subscriptions[$sid] = $true
    }
    $watchers[$Root] = $fsw
    Emit-CarrierEvent -Drive $DriveName -Root $Root -Change "DRIVE_BOUND" -Path $Root
  } catch {
    Emit-CarrierEvent -Drive $DriveName -Root $Root -Change "WATCH_ERROR" -Path $Root -Detail $_.Exception.Message
  }
}

function Refresh-Drives {
  $current = @{}
  Get-PSDrive -PSProvider FileSystem -ErrorAction SilentlyContinue | ForEach-Object {
    if ([string]::IsNullOrWhiteSpace($_.Root)) { return }
    $root = $_.Root
    $current[$root] = $_.Name
    Bind-DriveWatcher -DriveName $_.Name -Root $root
  }

  foreach ($root in @($watchers.Keys)) {
    if (-not $current.ContainsKey($root)) {
      try { $watchers[$root].EnableRaisingEvents = $false; $watchers[$root].Dispose() } catch {}
      $watchers.Remove($root)
      Emit-CarrierEvent -Drive "" -Root $root -Change "DRIVE_UNBOUND" -Path $root
    }
  }
}

try {
  Refresh-Drives
  $lastRefresh = Get-Date

  while ($true) {
    if (((Get-Date) - $lastRefresh).TotalSeconds -ge 30) {
      Refresh-Drives
      $lastRefresh = Get-Date
    }

    foreach ($ev in @(Get-Event -ErrorAction SilentlyContinue)) {
      if (-not $ev.SourceIdentifier.StartsWith("GGDV_CARRIER::")) { continue }

      $m = [regex]::Match($ev.SourceIdentifier, '^GGDV_CARRIER::([^:]+)::(.+)$')
      if (-not $m.Success) { continue }
      $drive = $m.Groups[1].Value
      $eventName = $m.Groups[2].Value
      $root = if ($drive) { "${drive}:\\" } else { "" }
      $args = $ev.SourceEventArgs

      $change = $eventName.ToUpperInvariant()
      $path = ""
      $oldPath = ""
      $detail = ""

      if ($eventName -eq "Error") {
        $change = "WATCH_ERROR"
        try { $detail = $args.GetException().Message } catch { $detail = "UNKNOWN_WATCH_ERROR" }
      } else {
        try { $path = $args.FullPath } catch {}
        if ($eventName -eq "Renamed") {
          try { $oldPath = $args.OldFullPath } catch {}
        }
      }

      $key = "$change|$path|$oldPath"
      $now = [DateTime]::UtcNow
      $emit = $true
      if ($recent.ContainsKey($key)) {
        if (($now - $recent[$key]).TotalMilliseconds -lt 500) { $emit = $false }
      }
      $recent[$key] = $now

      if ($emit) {
        Emit-CarrierEvent -Drive $drive -Root $root -Change $change -Path $path -OldPath $oldPath -Detail $detail
      }
      Remove-Event -EventIdentifier $ev.EventIdentifier -ErrorAction SilentlyContinue
    }

    foreach ($k in @($recent.Keys)) {
      if (([DateTime]::UtcNow - $recent[$k]).TotalSeconds -gt 10) { $recent.Remove($k) }
    }

    Start-Sleep -Milliseconds 200
  }
} finally {
  foreach ($sid in @($subscriptions.Keys)) {
    Unregister-Event -SourceIdentifier $sid -ErrorAction SilentlyContinue
  }
  foreach ($fsw in @($watchers.Values)) {
    try { $fsw.EnableRaisingEvents = $false; $fsw.Dispose() } catch {}
  }
  try { Remove-Item -LiteralPath $PidFile -Force -ErrorAction SilentlyContinue } catch {}
}