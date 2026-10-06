param(
  [Parameter(Mandatory=$true)][string]$OldRepo,
  [Parameter(Mandatory=$true)][string]$NewName,
  [string]$Owner = "2708halinh-cloud"
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
  throw "gh CLI not found"
}

$auth = gh auth status 2>&1 | Out-String
if ($LASTEXITCODE -ne 0) {
  throw "gh auth is not ready: $auth"
}

$oldFull = if ($OldRepo -match "/") { $OldRepo } else { "$Owner/$OldRepo" }
$body = @{ name = $NewName } | ConvertTo-Json -Compress

Write-Host "Renaming $oldFull -> $NewName"
$result = gh api -X PATCH "repos/$oldFull" --input - <<< $body
if ($LASTEXITCODE -ne 0) { throw "GitHub rename failed" }

$newFull = "$Owner/$NewName"
$readback = gh api "repos/$newFull" | ConvertFrom-Json
if ($readback.full_name -ne $newFull) {
  throw "Readback mismatch: expected $newFull got $($readback.full_name)"
}

$receipt = [ordered]@{
  schema = "GGDV_REPO_RENAME_RECEIPT/1.0"
  old_repo = $oldFull
  new_repo = $readback.full_name
  html_url = $readback.html_url
  default_branch = $readback.default_branch
  observed_at = (Get-Date).ToString("o")
  provider_readback = "PASS"
}

$receipt | ConvertTo-Json -Depth 6
