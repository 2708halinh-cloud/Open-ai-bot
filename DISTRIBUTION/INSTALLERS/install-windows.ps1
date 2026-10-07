$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$manifest = Get-Content -Raw -LiteralPath (Join-Path $Root "SOL_LONG_MACH.manifest.json") | ConvertFrom-Json
$modelArchive = Join-Path $Root $manifest.model.package
if (-not (Test-Path -LiteralPath $modelArchive)) { throw "Model package missing: $modelArchive" }
$modelVersion = $manifest.model.commit.Substring(0,8)
$modelHome = Join-Path $env:LOCALAPPDATA ("SOL_LONG_MACH\model\" + $modelVersion)
New-Item -ItemType Directory -Force -Path $modelHome | Out-Null
if (-not (Test-Path -LiteralPath (Join-Path $modelHome "AGENTS.md"))) { Expand-Archive -LiteralPath $modelArchive -DestinationPath $modelHome -Force }
$installerDir = Join-Path $Root "INSTALLERS\windows"
$msi = Get-ChildItem -LiteralPath $installerDir -Filter *.msi -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$exe = Get-ChildItem -LiteralPath $installerDir -Filter *.exe -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$appAction = "NO_INSTALLER_FOUND"
if ($msi) {
  $p = Start-Process msiexec.exe -ArgumentList @("/i", $msi.FullName, "/passive", "/norestart") -Wait -PassThru
  if ($p.ExitCode -ne 0) { throw "MSI install failed: $($p.ExitCode)" }
  $appAction = "MSI_INSTALLED"
} elseif ($exe) {
  $p = Start-Process $exe.FullName -Wait -PassThru
  if ($p.ExitCode -ne 0) { throw "EXE install failed: $($p.ExitCode)" }
  $appAction = "EXE_INSTALLED"
}
$receiptDir = Join-Path $env:LOCALAPPDATA "SOL_LONG_MACH"
New-Item -ItemType Directory -Force -Path $receiptDir | Out-Null
[ordered]@{
  schema="SOL_LONG_MACH_INSTALL_RECEIPT/1.0"; platform="windows-x64"; app_action=$appAction;
  model_home=$modelHome; model_commit=$manifest.model.commit; model_sha256=$manifest.model.sha256;
  installed_at=(Get-Date).ToString("o")
} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $receiptDir "install-receipt.json") -Encoding UTF8
Write-Host "SOL LONG MACH model materialized at $modelHome"
Write-Host "App action: $appAction"