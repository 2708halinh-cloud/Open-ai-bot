param(
  [Parameter(Mandatory=$true)][string]$ImagePath,
  [Parameter(Mandatory=$true)][string]$ExpectedSha256,
  [Parameter(Mandatory=$true)][Int64]$ExpectedSize,
  [Parameter(Mandatory=$true)][string]$ReceiptPath,
  [Parameter(Mandatory=$true)][string]$IdentityPath,
  [string]$PreferredDriveLetter = "G",
  [ValidateSet("TRUE","FALSE")][string]$AllowIdentityBootstrap = "TRUE",
  [ValidateSet("TRUE","FALSE")][string]$RequireUsb = "TRUE",
  [ValidateSet("TRUE","FALSE")][string]$ForbidSystemDisk = "TRUE",
  [ValidateSet("TRUE","FALSE")][string]$RebootToFirmware = "TRUE"
)

$ErrorActionPreference = "Stop"

function Fail([string]$Message) {
  Write-Error $Message
  exit 1
}

function As-Bool([string]$Value) {
  return $Value.ToUpperInvariant() -eq "TRUE"
}

function Normalize-Text($Value) {
  if ($null -eq $Value) { return "" }
  return ([string]$Value).Trim()
}

function Same-Text($A, $B) {
  $aa = Normalize-Text $A
  $bb = Normalize-Text $B
  if (-not $aa -or -not $bb) { return $false }
  return $aa.Equals($bb, [System.StringComparison]::OrdinalIgnoreCase)
}

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
  $self = $MyInvocation.MyCommand.Path
  $args = @(
    "-NoProfile","-ExecutionPolicy","Bypass","-File","`"$self`"",
    "-ImagePath","`"$ImagePath`"",
    "-ExpectedSha256","$ExpectedSha256",
    "-ExpectedSize","$ExpectedSize",
    "-ReceiptPath","`"$ReceiptPath`"",
    "-IdentityPath","`"$IdentityPath`"",
    "-PreferredDriveLetter","$PreferredDriveLetter",
    "-AllowIdentityBootstrap","$AllowIdentityBootstrap",
    "-RequireUsb","$RequireUsb",
    "-ForbidSystemDisk","$ForbidSystemDisk",
    "-RebootToFirmware","$RebootToFirmware"
  )
  $p = Start-Process powershell.exe -Verb RunAs -ArgumentList $args -Wait -PassThru
  exit $p.ExitCode
}

if (-not (Test-Path -LiteralPath $ImagePath)) { Fail "Image not found: $ImagePath" }
$img = Get-Item -LiteralPath $ImagePath
if ($img.Length -ne $ExpectedSize) { Fail "Image size mismatch: actual=$($img.Length) expected=$ExpectedSize" }
$sha = (Get-FileHash -Algorithm SHA256 -LiteralPath $ImagePath).Hash.ToLowerInvariant()
if ($sha -ne $ExpectedSha256.ToLowerInvariant()) { Fail "Image SHA256 mismatch" }

$identityDir = Split-Path -Parent $IdentityPath
if ($identityDir) { New-Item -ItemType Directory -Force -Path $identityDir | Out-Null }
$receiptDir = Split-Path -Parent $ReceiptPath
if ($receiptDir) { New-Item -ItemType Directory -Force -Path $receiptDir | Out-Null }

$targetIdentity = $null
$disk = $null
$bootstrapUsed = $false
$resolvedBy = $null

if (Test-Path -LiteralPath $IdentityPath) {
  try {
    $targetIdentity = Get-Content -LiteralPath $IdentityPath -Raw | ConvertFrom-Json
  } catch {
    Fail "Target identity file is unreadable: $IdentityPath"
  }

  $disks = @(Get-Disk)
  $matches = @()

  $uid = Normalize-Text $targetIdentity.disk_unique_id
  $serial = Normalize-Text $targetIdentity.disk_serial_number
  $size = [Int64]$targetIdentity.disk_size
  $friendly = Normalize-Text $targetIdentity.disk_friendly_name

  if ($uid) {
    $matches = @($disks | Where-Object { Same-Text $_.UniqueId $uid })
    $resolvedBy = "disk_unique_id"
  }

  if ($matches.Count -eq 0 -and $serial) {
    $matches = @($disks | Where-Object {
      (Same-Text $_.SerialNumber $serial) -and ([Int64]$_.Size -eq $size)
    })
    $resolvedBy = "serial_number+size"
  }

  if ($matches.Count -eq 0 -and $friendly -and $size -gt 0) {
    $matches = @($disks | Where-Object {
      (Same-Text $_.FriendlyName $friendly) -and ([Int64]$_.Size -eq $size) -and ([string]$_.BusType -eq "USB")
    })
    $resolvedBy = "friendly_name+size+usb"
  }

  if ($matches.Count -ne 1) {
    Fail "Persisted target identity did not resolve to exactly one disk (matches=$($matches.Count)). Refusing drive-letter fallback."
  }
  $disk = $matches[0]
} else {
  if (-not (As-Bool $AllowIdentityBootstrap)) {
    Fail "No target identity exists and bootstrap is disabled."
  }

  $letter = $PreferredDriveLetter.Trim().TrimEnd(":")
  if (-not $letter) { Fail "PreferredDriveLetter is empty" }

  $partition = Get-Partition -DriveLetter $letter -ErrorAction Stop
  $disk = Get-Disk -Number $partition.DiskNumber -ErrorAction Stop
  $bootstrapUsed = $true
  $resolvedBy = "preferred_drive_letter_bootstrap"
}

if ((As-Bool $ForbidSystemDisk) -and ($disk.IsBoot -or $disk.IsSystem)) {
  Fail "Resolved target maps to Windows boot/system disk"
}
if ($disk.IsReadOnly) { Fail "Resolved target disk is read-only" }
if ((As-Bool $RequireUsb) -and ([string]$disk.BusType -ne "USB")) {
  Fail "Resolved target is not USB; BusType=$($disk.BusType)"
}
if ($disk.Size -lt $img.Length) {
  Fail "Resolved USB is smaller than the boot image"
}

$diskNumber = [int]$disk.Number
$partitions = @(Get-Partition -DiskNumber $diskNumber -ErrorAction SilentlyContinue)
$driveLetters = @(
  $partitions |
    Where-Object { $_.DriveLetter } |
    ForEach-Object { ([string]$_.DriveLetter).Trim().ToUpperInvariant() } |
    Sort-Object -Unique
)

$bootstrapVolume = $null
if ($bootstrapUsed) {
  $letter = $PreferredDriveLetter.Trim().TrimEnd(":")
  try { $bootstrapVolume = Get-Volume -DriveLetter $letter -ErrorAction Stop } catch {}
}

$identityRecord = [ordered]@{
  schema = "TESSERACT_OS_BOOT_TARGET_IDENTITY/1.0"
  disk_unique_id = Normalize-Text $disk.UniqueId
  disk_serial_number = Normalize-Text $disk.SerialNumber
  disk_friendly_name = Normalize-Text $disk.FriendlyName
  disk_size = [Int64]$disk.Size
  bus_type = [string]$disk.BusType
  bootstrap_drive_letter = if ($bootstrapUsed) { "$($PreferredDriveLetter.Trim().TrimEnd(':').ToUpperInvariant()):" } elseif ($targetIdentity) { $targetIdentity.bootstrap_drive_letter } else { $null }
  bootstrap_volume_unique_id = if ($bootstrapVolume) { Normalize-Text $bootstrapVolume.UniqueId } elseif ($targetIdentity) { $targetIdentity.bootstrap_volume_unique_id } else { "" }
  last_observed_drive_letters = $driveLetters
  observed_at = (Get-Date).ToString("o")
}

if (-not $identityRecord.disk_unique_id -and -not $identityRecord.disk_serial_number) {
  if (-not $identityRecord.disk_friendly_name -or $identityRecord.disk_size -le 0) {
    Fail "Target lacks sufficient stable identity fields"
  }
}

$identityRecord | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $IdentityPath -Encoding UTF8

$devicePath = "\\.\PhysicalDrive$diskNumber"

foreach ($driveLetter in $driveLetters) {
  & mountvol.exe "$driveLetter`:" /p | Out-Null
  if ($LASTEXITCODE -ne 0) {
    Fail "Unable to dismount $driveLetter`: on resolved target disk"
  }
}
Start-Sleep -Milliseconds 800

$bufferSize = 4MB
$buffer = New-Object byte[] $bufferSize
$imageStream = $null
$diskStream = $null
try {
  $imageStream = [System.IO.File]::Open(
    $ImagePath,
    [System.IO.FileMode]::Open,
    [System.IO.FileAccess]::Read,
    [System.IO.FileShare]::Read
  )
  $diskStream = New-Object System.IO.FileStream(
    $devicePath,
    [System.IO.FileMode]::Open,
    [System.IO.FileAccess]::ReadWrite,
    [System.IO.FileShare]::ReadWrite,
    $bufferSize,
    [System.IO.FileOptions]::WriteThrough
  )
  $diskStream.Position = 0
  [Int64]$written = 0
  while (($read = $imageStream.Read($buffer,0,$buffer.Length)) -gt 0) {
    $diskStream.Write($buffer,0,$read)
    $written += $read
    $pct = [Math]::Min(100,[Math]::Round(($written * 100.0) / $img.Length,1))
    Write-Progress -Activity "Writing TESSERACT OS to resolved USB target" -Status "$pct%" -PercentComplete $pct
  }
  $diskStream.Flush($true)
  Write-Progress -Activity "Writing TESSERACT OS to resolved USB target" -Completed
} finally {
  if ($diskStream) { $diskStream.Dispose() }
  if ($imageStream) { $imageStream.Dispose() }
}

$hash = [System.Security.Cryptography.SHA256]::Create()
$src = $null
try {
  $src = New-Object System.IO.FileStream(
    $devicePath,
    [System.IO.FileMode]::Open,
    [System.IO.FileAccess]::Read,
    [System.IO.FileShare]::ReadWrite,
    $bufferSize,
    [System.IO.FileOptions]::SequentialScan
  )
  [Int64]$remaining = $img.Length
  while ($remaining -gt 0) {
    $want = [int][Math]::Min($buffer.Length,$remaining)
    $read = $src.Read($buffer,0,$want)
    if ($read -le 0) { Fail "Unexpected end of device during readback" }
    [void]$hash.TransformBlock($buffer,0,$read,$null,0)
    $remaining -= $read
  }
  [void]$hash.TransformFinalBlock([byte[]]::new(0),0,0)
  $readbackSha = ([BitConverter]::ToString($hash.Hash)).Replace("-","").ToLowerInvariant()
} finally {
  if ($src) { $src.Dispose() }
  $hash.Dispose()
}
if ($readbackSha -ne $ExpectedSha256.ToLowerInvariant()) {
  Fail "Raw readback SHA256 mismatch"
}

$receipt = [ordered]@{
  schema = "TESSERACT_OS_LOCAL_BOOT_RECEIPT/2.0"
  target_identity_path = ".runtime/TESSERACT_BOOT_TARGET_IDENTITY.json"
  target_resolution = $resolvedBy
  preferred_drive_letter = "$($PreferredDriveLetter.Trim().TrimEnd(':').ToUpperInvariant()):"
  bootstrap_used = $bootstrapUsed
  physical_disk = $diskNumber
  target_identity_bound = $true
  bus_type = [string]$disk.BusType
  drive_letters_before_write = $driveLetters
  image = $img.Name
  image_size = $img.Length
  image_sha256 = $sha
  readback_sha256 = $readbackSha
  write_verified = $true
  boot_path = "EFI/BOOT/BOOTX64.EFI"
  next_action = "UEFI_FIRMWARE_BOOT"
  timestamp = (Get-Date).ToString("o")
}
$receipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $ReceiptPath -Encoding UTF8

if (As-Bool $RebootToFirmware) {
  shutdown.exe /r /fw /t 8 /c "TESSERACT OS: boot resolved USB target from firmware"
}
