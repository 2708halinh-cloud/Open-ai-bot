param(
  [string]$SnapshotReceipt = "",
  [string]$DriveRoot = $env:GGDV_DRIVE_ROOT,
  [switch]$ApplyArchive
)

$ErrorActionPreference = "Stop"

$workspace = (Resolve-Path (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "..")).Path
if (-not $SnapshotReceipt) {
  $SnapshotReceipt = Join-Path $workspace ".runtime\AGENT_CARRIER_SNAPSHOT_RECEIPT_CURRENT.json"
}
if (-not (Test-Path -LiteralPath $SnapshotReceipt)) {
  throw "Snapshot receipt not found: $SnapshotReceipt"
}

if (-not $DriveRoot) {
  foreach ($candidate in @(
    "W:\Drive của tôi",
    "G:\Drive của tôi",
    "/mnt/w/Drive của tôi",
    "/mnt/g/Drive của tôi"
  )) {
    if (Test-Path -LiteralPath $candidate) {
      $DriveRoot = (Resolve-Path -LiteralPath $candidate).Path
      break
    }
  }
}
if (-not $DriveRoot) { throw "Drive root not found. Set GGDV_DRIVE_ROOT." }

$receipt = Get-Content -Raw -LiteralPath $SnapshotReceipt | ConvertFrom-Json
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$archiveRoot = Join-Path $DriveRoot "__GGDV_ARCHIVE_AFTER_GITHUB_SNAPSHOT"

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

$cleanup = [ordered]@{
  schema = "GGDV_DRIVE_CLEANUP_RECEIPT/1.0"
  observed_at = (Get-Date).ToString("o")
  mode = if ($ApplyArchive) { "ARCHIVE_APPLY" } else { "PLAN_ONLY" }
  source_snapshot_receipt = $SnapshotReceipt
  archive_root = $archiveRoot
  items = @()
}

foreach ($agentItem in $receipt.agents) {
  $item = [ordered]@{
    agent = $agentItem.agent
    snapshot_state = $agentItem.state
    git_commit = $agentItem.git_commit
    source = $agentItem.source
    eligible = $false
    action = "NONE"
    archive_path = $null
    error = $null
  }

  if ($agentItem.state -ne "SNAPSHOT_PASS" -or $agentItem.provider_readback -ne "PASS") {
    $item.action = "KEEP_CURRENT_NOT_ELIGIBLE"
    $cleanup.items += $item
    continue
  }

  $rel = $sourceMap[[string]$agentItem.agent]
  if (-not $rel) {
    $item.action = "KEEP_CURRENT_NO_SOURCE_MAP"
    $cleanup.items += $item
    continue
  }

  $src = Join-Path $DriveRoot $rel
  if (-not (Test-Path -LiteralPath $src)) {
    $item.action = "KEEP_CURRENT_SOURCE_NOT_MOUNTED"
    $cleanup.items += $item
    continue
  }

  $item.eligible = $true
  $dest = Join-Path (Join-Path $archiveRoot ([string]$agentItem.agent)) $stamp
  $item.archive_path = $dest

  if ($ApplyArchive) {
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dest) | Out-Null
    Move-Item -LiteralPath $src -Destination $dest
    $item.action = "MOVED_TO_ARCHIVE"
  } else {
    $item.action = "ARCHIVE_PLANNED"
  }

  $cleanup.items += $item
}

$out = Join-Path $workspace ".runtime\DRIVE_CLEANUP_RECEIPT_CURRENT.json"
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $out) | Out-Null
$cleanup | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $out -Encoding UTF8
Write-Host "Receipt: $out"
