param(
  [Parameter(Mandatory=$true)][string]$TargetRepoDir,
  [Parameter(Mandatory=$true)][string]$SourceRelativePath,
  [string]$DriveRoot = $env:GGDV_DRIVE_ROOT,
  [string]$Branch = "main"
)

$ErrorActionPreference = "Stop"

function Resolve-DriveRoot {
  param([string]$Explicit)
  $candidates = @()
  if ($Explicit) { $candidates += $Explicit }
  if ($env:GGDV_DRIVE_ROOT) { $candidates += $env:GGDV_DRIVE_ROOT }
  $candidates += @(
    "W:\Drive của tôi",
    "G:\Drive của tôi",
    "/mnt/w/Drive của tôi",
    "/mnt/g/Drive của tôi"
  )
  foreach ($c in $candidates) {
    if ($c -and (Test-Path -LiteralPath $c)) {
      return (Resolve-Path -LiteralPath $c).Path
    }
  }
  throw "Drive root not found. Set GGDV_DRIVE_ROOT."
}

$drive = Resolve-DriveRoot $DriveRoot
$src = Join-Path $drive $SourceRelativePath
if (-not (Test-Path -LiteralPath $src)) {
  throw "Source tree not found: $src"
}
if (-not (Test-Path -LiteralPath $TargetRepoDir)) {
  throw "Target repo dir not found: $TargetRepoDir"
}

Push-Location $TargetRepoDir
try {
  if (-not (Test-Path ".git")) { throw "Target is not a Git repo: $TargetRepoDir" }

  $dest = Join-Path $TargetRepoDir "agent-data"
  New-Item -ItemType Directory -Force -Path $dest | Out-Null

  $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
  $metaDir = Join-Path $TargetRepoDir ".ggdv-migration"
  New-Item -ItemType Directory -Force -Path $metaDir | Out-Null

  if (Get-Command robocopy -ErrorAction SilentlyContinue) {
    robocopy $src $dest /E /COPY:DAT /DCOPY:DAT /R:2 /W:2 /XJ /XD ".git" | Out-Host
    if ($LASTEXITCODE -ge 8) { throw "robocopy failed with exit $LASTEXITCODE" }
  } elseif (Get-Command rsync -ErrorAction SilentlyContinue) {
    & rsync -a --exclude ".git" "$src/" "$dest/"
    if ($LASTEXITCODE -ne 0) { throw "rsync failed" }
  } else {
    Copy-Item -LiteralPath (Join-Path $src "*") -Destination $dest -Recurse -Force
  }

  $manifest = [ordered]@{
    schema = "GGDV_DRIVE_TREE_TO_REPO/1.0"
    source_root = $drive
    source_relative_path = $SourceRelativePath
    destination = "agent-data"
    migrated_at = (Get-Date).ToString("o")
    history_preserved = $true
  }
  $manifestPath = Join-Path $metaDir "MIGRATION_$stamp.json"
  $manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $manifestPath -Encoding UTF8

  git add agent-data .ggdv-migration
  git commit -m "Import agent data from Drive tree: $SourceRelativePath"
  if ($LASTEXITCODE -ne 0) {
    Write-Host "No new Git commit created; inspect git status."
  }
  git push origin $Branch

  $head = git rev-parse HEAD
  [ordered]@{
    schema = "GGDV_DRIVE_TREE_TO_REPO_RECEIPT/1.0"
    source = $src
    repo = (git remote get-url origin)
    branch = $Branch
    head = $head
    migrated_at = (Get-Date).ToString("o")
  } | ConvertTo-Json -Depth 8
} finally {
  Pop-Location
}
