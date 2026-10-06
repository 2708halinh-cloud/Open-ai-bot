param(
  [string]$Distro = 'Ubuntu'
)
$ErrorActionPreference = 'Stop'
$identity=[Security.Principal.WindowsIdentity]::GetCurrent()
$principal=New-Object Security.Principal.WindowsPrincipal($identity)
if(-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){
  Start-Process powershell.exe -Verb RunAs -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',"`"$($MyInvocation.MyCommand.Path)`"")
  exit
}
$TaskName='TESSERACT_LOCAL_BRIDGE'
$WslRoot='/home/halin/kepler/worktrees/Open-ai-bot-2-unify-item-matrix-34d45d00'
$arg="-d $Distro -- bash -lc `"cd '$WslRoot' && exec python3 LOCAL_BRIDGE/bridge.py`""
$action=New-ScheduledTaskAction -Execute 'wsl.exe' -Argument $arg
$trigger=New-ScheduledTaskTrigger -AtLogOn
$settings=New-ScheduledTaskSettingsSet -StartWhenAvailable -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1)
$principalSpec=New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Principal $principalSpec -Force | Out-Null
Start-ScheduledTask -TaskName $TaskName
Write-Host 'TESSERACT_LOCAL_BRIDGE_STARTED'
