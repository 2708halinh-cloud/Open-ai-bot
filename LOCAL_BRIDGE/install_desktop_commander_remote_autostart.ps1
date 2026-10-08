param(
  [switch]$StartNow = $true
)

$ErrorActionPreference = 'Stop'

$taskName = 'DesktopCommanderRemote'
$base = Join-Path $env:LOCALAPPDATA 'DesktopCommanderRemote'
$launcher = Join-Path $base 'start-remote.ps1'
$log = Join-Path $base 'remote.log'
New-Item -ItemType Directory -Force -Path $base | Out-Null

$npx = (Get-Command npx.cmd -ErrorAction Stop).Source

$launcherContent = @'
$ErrorActionPreference = 'Stop'
$base = Join-Path $env:LOCALAPPDATA 'DesktopCommanderRemote'
$log = Join-Path $base 'remote.log'
New-Item -ItemType Directory -Force -Path $base | Out-Null

try {
  $existing = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object {
      $_.CommandLine -and
      $_.CommandLine -match 'desktop-commander' -and
      $_.CommandLine -match '(^|\s)remote(\s|$)'
    }

  if ($existing) {
    Add-Content -LiteralPath $log -Value ("{0} ALREADY_RUNNING pid={1}" -f (Get-Date).ToString('o'), (($existing.ProcessId -join ',')))
    exit 0
  }

  $npx = (Get-Command npx.cmd -ErrorAction Stop).Source
  Add-Content -LiteralPath $log -Value ("{0} START {1} -y @wonderwhy-er/desktop-commander@latest remote" -f (Get-Date).ToString('o'), $npx)

  & $npx -y '@wonderwhy-er/desktop-commander@latest' remote *>> $log
  $code = $LASTEXITCODE
  Add-Content -LiteralPath $log -Value ("{0} EXIT code={1}" -f (Get-Date).ToString('o'), $code)
  exit $code
} catch {
  Add-Content -LiteralPath $log -Value ("{0} ERROR {1}" -f (Get-Date).ToString('o'), $_.Exception.Message)
  exit 1
}
'@

Set-Content -LiteralPath $launcher -Value $launcherContent -Encoding UTF8

$user = if ($env:USERDOMAIN) { "$env:USERDOMAIN\$env:USERNAME" } else { $env:USERNAME }
$ps = (Get-Command powershell.exe -ErrorAction Stop).Source
$arguments = '-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "' + $launcher + '"'

$action = New-ScheduledTaskAction -Execute $ps -Argument $arguments
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $user
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -RestartCount 5 -RestartInterval (New-TimeSpan -Minutes 1) -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Days 0)
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description 'Auto-start Desktop Commander Remote at Windows logon using npx @wonderwhy-er/desktop-commander@latest remote' -Force | Out-Null

if ($StartNow) {
  Start-ScheduledTask -TaskName $taskName
  Start-Sleep -Seconds 8
}

$task = Get-ScheduledTask -TaskName $taskName
$info = Get-ScheduledTaskInfo -TaskName $taskName
$running = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
  Where-Object {
    $_.CommandLine -and
    $_.CommandLine -match 'desktop-commander' -and
    $_.CommandLine -match '(^|\s)remote(\s|$)'
  } |
  Select-Object -First 5 ProcessId, Name, CommandLine

$receipt = [ordered]@{
  schema = 'DESKTOP_COMMANDER_REMOTE_AUTOSTART/1.0'
  observed_at = (Get-Date).ToString('o')
  computer = $env:COMPUTERNAME
  user = $user
  task_name = $taskName
  launcher = $launcher
  npx = $npx
  task_state = [string]$task.State
  last_run_time = $info.LastRunTime
  last_task_result = $info.LastTaskResult
  next_run_time = $info.NextRunTime
  running_processes = @($running)
  status = if ($running) { 'INSTALLED_AND_RUNNING' } else { 'INSTALLED_PROCESS_NOT_YET_OBSERVED' }
}

$receiptPath = Join-Path $base 'install-receipt.json'
$receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $receiptPath -Encoding UTF8
$receipt | ConvertTo-Json -Depth 8
