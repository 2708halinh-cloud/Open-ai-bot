param(
  [switch]$EnableMotor,
  [string]$AppAdapter = ""
)
$ErrorActionPreference = "Stop"
$PluginRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
if ($EnableMotor) { $env:GGDV_MOTOR_ENABLE = "1" } else { $env:GGDV_MOTOR_ENABLE = "0" }
if ($AppAdapter) { $env:GGDV_APP_ADAPTER = $AppAdapter }
python "$PluginRoot\server\motor_mcp.py"
