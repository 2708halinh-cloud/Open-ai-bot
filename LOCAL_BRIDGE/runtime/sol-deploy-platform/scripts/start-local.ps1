$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root
if ($env:PYTHONPATH) {
  $env:PYTHONPATH = "$Root;$env:PYTHONPATH"
} else {
  $env:PYTHONPATH = $Root
}
python -m sol_deploy.cli serve @args
