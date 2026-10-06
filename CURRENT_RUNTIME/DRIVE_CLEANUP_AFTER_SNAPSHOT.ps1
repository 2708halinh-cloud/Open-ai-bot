param(
  [string]$SnapshotReceipt = "",
  [string]$DriveRoot = $env:GGDV_DRIVE_ROOT,
  [switch]$ApplyArchive
)

$ErrorActionPreference = "Stop"

if ($ApplyArchive) {
  throw "ARCHIVE_DISABLED: chế độ di chuyển dữ liệu đã bị vô hiệu hóa. Chỉ cho phép lập kế hoạch, đọc, băm, snapshot và kiểm chứng."
}

$workspace = (Resolve-Path (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "..")).Path
if (-not $SnapshotReceipt) {
  $SnapshotReceipt = Join-Path $workspace ".runtime\AGENT_CARRIER_SNAPSHOT_RECEIPT_CURRENT.json"
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

$protected = @(
  "HÀ LINH - NGUYÊN THỦY THIÊN TÔN"
)

$receipt = [ordered]@{
  schema = "GGDV_DRIVE_CLEANUP_PLAN/2.0"
  observed_at = (Get-Date).ToString("o")
  mode = "PLAN_ONLY"
  apply_archive = $false
  drive_root = $DriveRoot
  snapshot_receipt = $SnapshotReceipt
  protected_roots = $protected
  allowed_actions = @("READ","HASH","INDEX","SNAPSHOT","COPY_TO_SANDBOX")
  forbidden_actions = @("MOVE_SOURCE","DELETE_SOURCE","OVERWRITE_SOURCE","DESTRUCTIVE_TEST")
  note = "Script này không còn chứa hành động di chuyển/xóa nguồn."
}

$out = Join-Path $workspace ".runtime\DRIVE_CLEANUP_PLAN_CURRENT.json"
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $out) | Out-Null
$receipt | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $out -Encoding UTF8
Write-Host "Đã lập kế hoạch an toàn: $out"
