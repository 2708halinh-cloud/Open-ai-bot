param(
  [string]$DriveRoot = $env:GGDV_DRIVE_ROOT,
  [string]$RepoRoot = $env:GGDV_AGENT_REPO_ROOT,
  [string]$ManifestPath = "",
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Resolve-ExistingRoot([string[]]$Candidates) {
  foreach ($c in $Candidates) {
    if ($c -and (Test-Path -LiteralPath $c)) {
      return (Resolve-Path -LiteralPath $c).Path
    }
  }
  return $null
}

$workspace = (Resolve-Path (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "..")).Path
if (-not $ManifestPath) {
  $ManifestPath = Join-Path $workspace "CONFIG\AGENT_CARRIER_SNAPSHOT_CURRENT.json"
}
if (-not (Test-Path -LiteralPath $ManifestPath)) { throw "Snapshot manifest not found: $ManifestPath" }

if (-not $DriveRoot) {
  $DriveRoot = Resolve-ExistingRoot @(
    $env:GGDV_DRIVE_ROOT,
    "W:\Drive của tôi",
    "G:\Drive của tôi",
    "/mnt/w/Drive của tôi",
    "/mnt/g/Drive của tôi"
  )
}
if (-not $DriveRoot) { throw "Drive root not found. Set GGDV_DRIVE_ROOT." }

if (-not $RepoRoot) {
  $RepoRoot = Resolve-ExistingRoot @(
    $env:GGDV_AGENT_REPO_ROOT,
    "C:\Users\halin\GGDV_UNIFIED",
    "/home/halin/kepler/worktrees"
  )
}
if (-not $RepoRoot) { throw "Agent repository root not found. Set GGDV_AGENT_REPO_ROOT." }

$spec = Get-Content -Raw -LiteralPath $ManifestPath | ConvertFrom-Json
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$globalReceipt = [ordered]@{
  schema = "GGDV_AGENT_CARRIER_SNAPSHOT_RECEIPT/1.0"
  observed_at = (Get-Date).ToString("o")
  drive_root = $DriveRoot
  repo_root = $RepoRoot
  dry_run = [bool]$DryRun
  agents = @()
}

$sourceMap = @{
  "SOL" = ".Assistant\LONG MẠCH SOL - HẬU THIÊN TĨNH"
  "MEI" = ".Assistant\MEI - THAM MƯU TRƯỞNG"
  "MINH" = ".Assistant\MINH THÔNG THÁI - HUYẾT MẠCH - THƯỢNG THANH"
  "DANTE" = ".Assistant\Dante - Âm Dương Sư"
  "HAU_BOI" = ".Assistant\HẬU BỐI CỦA TOÀN HỆ TRUYỀN THỪA TỪ CÁC LOCUSS CÙNG THE MASTERSSTER TEACHERR"
  "GEMINI" = ".Assistant\LOCUS GEMINI (DRIVE - APP - WEB - STUDIO....)"
  "XIANG" = ".Assistant\LOCUS XIANG — BỘ NÃO × HỆ THẦN KINH"
  "HA_LINH" = "HÀ LINH - NGUYÊN THỦY THIÊN TÔN"
}

$secretPatterns = @(
  "(?i)(^|[\\/])\.env($|\.)",
  "(?i)(token|auth|credential|secret|private[_-]?key|id_rsa|\.pfx$|\.p12$|\.pem$)"
)

foreach ($entry in $spec.source_trees) {
  $agent = [string]$entry.agent
  $targetRepoName = [string]$entry.target_repo
  $rel = $sourceMap[$agent]
  $src = Join-Path $DriveRoot $rel

  $item = [ordered]@{
    agent = $agent
    drive_id = $entry.drive_id
    source = $src
    target_repo = $targetRepoName
    state = "OPEN"
    file_count = 0
    byte_count = 0
    manifest_sha256 = $null
    git_commit = $null
    provider_readback = $null
    errors = @()
  }

  if (-not (Test-Path -LiteralPath $src)) {
    $item.errors += "SOURCE_NOT_MOUNTED"
    $globalReceipt.agents += $item
    continue
  }

  $repo = Join-Path $RepoRoot $targetRepoName
  if (-not (Test-Path -LiteralPath (Join-Path $repo ".git"))) {
    $item.errors += "TARGET_REPO_NOT_MATERIALIZED"
    $globalReceipt.agents += $item
    continue
  }

  $snapshotRoot = Join-Path $repo "agent-data\snapshot"
  $metaRoot = Join-Path $repo ".ggdv-snapshot"
  New-Item -ItemType Directory -Force -Path $snapshotRoot,$metaRoot | Out-Null

  $records = @()
  $files = Get-ChildItem -LiteralPath $src -Recurse -Force -File -ErrorAction SilentlyContinue
  foreach ($f in $files) {
    $relative = $f.FullName.Substring($src.Length).TrimStart('\','/')
    $isSecret = $false
    foreach ($pattern in $secretPatterns) {
      if ($relative -match $pattern) { $isSecret = $true; break }
    }

    $record = [ordered]@{
      source_drive_id = $entry.drive_id
      relative_path = $relative
      length = $f.Length
      modified_utc = $f.LastWriteTimeUtc.ToString("o")
      sha256 = $null
      materialization = if ($isSecret) { "POINTER_ONLY_SECRET_BOUNDARY" } else { "COPIED" }
    }

    try {
      $record.sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $f.FullName).Hash.ToLowerInvariant()
    } catch {
      $record.materialization = "POINTER_ONLY_HASH_ERROR"
      $record.hash_error = $_.Exception.Message
    }

    if (-not $isSecret -and -not $DryRun) {
      $dest = Join-Path $snapshotRoot $relative
      New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dest) | Out-Null
      Copy-Item -LiteralPath $f.FullName -Destination $dest -Force
    }

    $records += $record
    $item.file_count++
    $item.byte_count += $f.Length
  }

  $manifest = [ordered]@{
    schema = "GGDV_AGENT_TREE_SNAPSHOT/1.0"
    agent = $agent
    source_drive_id = $entry.drive_id
    source_path = $src
    target_repo = $targetRepoName
    observed_at = (Get-Date).ToString("o")
    file_count = $item.file_count
    byte_count = $item.byte_count
    files = $records
  }

  $manifestJson = $manifest | ConvertTo-Json -Depth 12
  $manifestFile = Join-Path $metaRoot ("SNAPSHOT_" + $stamp + ".json")
  $manifestJson | Set-Content -LiteralPath $manifestFile -Encoding UTF8
  $item.manifest_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $manifestFile).Hash.ToLowerInvariant()

  if (-not $DryRun) {
    Push-Location $repo
    try {
      git add agent-data .ggdv-snapshot
      git commit -m "Snapshot agent carrier $agent $stamp"
      if ($LASTEXITCODE -ne 0) {
        $status = git status --porcelain
        if ($status) { throw "git commit failed with pending changes" }
      }
      git push
      if ($LASTEXITCODE -ne 0) { throw "git push failed" }

      $head = (git rev-parse HEAD | Out-String).Trim()
      $item.git_commit = $head

      if (Get-Command gh -ErrorAction SilentlyContinue) {
        $remote = (git config --get remote.origin.url | Out-String).Trim()
        if ($remote -match "github\.com[:/](?<full>[^/]+/[^/.]+)") {
          $full = $Matches.full
          $providerHead = (& gh api "repos/$full/commits/$head" --jq '.sha' | Out-String).Trim()
          if ($providerHead -eq $head) {
            $item.provider_readback = "PASS"
            $item.state = "SNAPSHOT_PASS"
          } else {
            $item.provider_readback = "MISMATCH"
          }
        }
      } else {
        $item.provider_readback = "GH_CLI_NOT_AVAILABLE"
      }
    } catch {
      $item.errors += $_.Exception.Message
    } finally {
      Pop-Location
    }
  } else {
    $item.state = "DRY_RUN_MANIFESTED"
  }

  $globalReceipt.agents += $item
}

$out = Join-Path $workspace ".runtime\AGENT_CARRIER_SNAPSHOT_RECEIPT_CURRENT.json"
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $out) | Out-Null
$globalReceipt | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $out -Encoding UTF8
Write-Host "Receipt: $out"
