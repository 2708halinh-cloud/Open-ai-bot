param(
  [switch]$SkipAtlassianLogin,
  [switch]$SkipDockerPull
)

$ErrorActionPreference = "Stop"

function Resolve-WorkspaceRoot {
  if ($env:GGDV_WORKSPACE_ROOT -and (Test-Path $env:GGDV_WORKSPACE_ROOT)) {
    return (Resolve-Path $env:GGDV_WORKSPACE_ROOT).Path
  }
  $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
  $candidate = Resolve-Path (Join-Path $scriptDir "..") -ErrorAction SilentlyContinue
  if ($candidate) { return $candidate.Path }
  return (Get-Location).Path
}

function Test-LocalPort([int]$Port) {
  try {
    return (Test-NetConnection -ComputerName 127.0.0.1 -Port $Port -WarningAction SilentlyContinue).TcpTestSucceeded
  } catch { return $false }
}

$root = Resolve-WorkspaceRoot
$vscode = Join-Path $root ".vscode"
$receiptDir = Join-Path $vscode "receipts"
New-Item -ItemType Directory -Force -Path $receiptDir | Out-Null

$receipt = [ordered]@{
  schema = "LOCAL_SOL_OPEN_SUPPORT/1.1"
  observed_at = (Get-Date).ToString("o")
  workspace_root = $root
  open_semantics = "DIRECT_SIGNAL_INGRESS_OPEN_PROPOSITION"
  actions = @()
  checks = [ordered]@{}
}

if (Get-Command code -ErrorAction SilentlyContinue) {
  $workspace = Join-Path $vscode "SOL_GGDV.code-workspace"
  if (Test-Path $workspace) {
    Start-Process code -ArgumentList @($workspace)
    $receipt.actions += "OPEN_VSCODE_WORKSPACE"
  } else {
    Start-Process code -ArgumentList @($root)
    $receipt.actions += "OPEN_VSCODE_ROOT"
  }
  $receipt.checks.code_cli = "PRESENT"
} else {
  $receipt.checks.code_cli = "MISSING"
}

$targets = @(
  @{Port=8765; Path=(Join-Path $vscode "device\nervous\nervous_api_server.py"); Args=@()},
  @{Port=8788; Path=(Join-Path $vscode "device\nervous\fastapi_mcp_server.py"); Args=@("8788")}
)
foreach ($t in $targets) {
  $before = Test-LocalPort $t.Port
  $receipt.checks["port_$($t.Port)_before"] = $before
  if (-not $before -and (Test-Path $t.Path)) {
    Start-Process python -ArgumentList (@($t.Path) + $t.Args) -WorkingDirectory (Split-Path -Parent $t.Path)
    $receipt.actions += "START_PORT_$($t.Port)"
  }
}

$workstationRun = Join-Path $vscode "device\GGDV_WORKSTATION\run.ps1"
if (-not (Test-LocalPort 8787) -and (Test-Path $workstationRun)) {
  Start-Process powershell -ArgumentList @("-ExecutionPolicy","Bypass","-File",$workstationRun) -WorkingDirectory (Split-Path -Parent $workstationRun)
  $receipt.actions += "START_GGDV_WORKSTATION_8787"
}

Start-Sleep -Seconds 2
foreach ($port in 8765,8787,8788) {
  $receipt.checks["port_$($port)_after"] = Test-LocalPort $port
}

$verify = Join-Path $vscode "verify_agent_sub_runtime.py"
if (Test-Path $verify) {
  $out = & python $verify 2>&1 | Out-String
  $receipt.checks.agent_sub_verify = $out.Trim()
  $receipt.actions += "RUN_AGENT_SUB_VERIFY"
}

if (Get-Command gh -ErrorAction SilentlyContinue) {
  $receipt.checks.gh_cli = "PRESENT"
  $receipt.checks.gh_auth_status = (& gh auth status 2>&1 | Out-String).Trim()
} else {
  $receipt.checks.gh_cli = "MISSING"
}

$mcpPath = Join-Path $vscode "mcp_config.json"
if (Test-Path $mcpPath) {
  $mcp = Get-Content -Raw -LiteralPath $mcpPath | ConvertFrom-Json
  if (-not $mcp.mcpServers) {
    $mcp | Add-Member -NotePropertyName mcpServers -NotePropertyValue ([ordered]@{})
  }
  if (-not $mcp.mcpServers.atlassian) {
    $mcp.mcpServers | Add-Member -NotePropertyName atlassian -NotePropertyValue ([ordered]@{
      type = "http"
      url = "https://mcp.atlassian.com/v2/mcp"
    })
    $mcp | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $mcpPath -Encoding UTF8
    $receipt.actions += "PATCH_MCP_CONFIG_ATLASSIAN"
  } else {
    $receipt.checks.atlassian_mcp_config = "ALREADY_PRESENT"
  }
}

if (Get-Command codex -ErrorAction SilentlyContinue) {
  $receipt.checks.codex_cli = "PRESENT"
  $list = & codex mcp list 2>&1 | Out-String
  $receipt.checks.codex_mcp_list = $list.Trim()
  if ($list -notmatch "(?i)atlassian") {
    $add = & codex mcp add atlassian --url https://mcp.atlassian.com/v2/mcp 2>&1 | Out-String
    $receipt.checks.codex_mcp_add = $add.Trim()
    $receipt.actions += "REGISTER_ATLASSIAN_MCP_CODEX"
  }
  if (-not $SkipAtlassianLogin) {
    try {
      $login = & codex mcp login atlassian 2>&1 | Out-String
      $receipt.checks.codex_mcp_login = $login.Trim()
      $receipt.actions += "ATLASSIAN_OAUTH_LOGIN_REQUESTED"
    } catch {
      $receipt.checks.codex_mcp_login = "OPEN: $($_.Exception.Message)"
    }
  }
} else {
  $receipt.checks.codex_cli = "MISSING"
}

$images = @(
  "amazon/cloudwatch-agent:latest",
  "datadog/agent:latest",
  "public.ecr.aws/aws-observability/aws-for-fluent-bit:latest",
  "public.ecr.aws/aws-observability/aws-otel-collector:latest",
  "public.ecr.aws/xray/aws-xray-daemon:latest",
  "public.ecr.aws/aws-cli/aws-cli:latest",
  "nginx:latest",
  "redis:latest",
  "python:latest",
  "node:latest",
  "postgres:latest",
  "mysql:latest",
  "mongo:latest",
  "alpine:latest",
  "busybox:latest",
  "ubuntu:latest",
  "docker:latest",
  "bash:latest",
  "golang:latest"
)

if (Get-Command docker -ErrorAction SilentlyContinue) {
  $receipt.checks.docker_cli = "PRESENT"
  if (-not $SkipDockerPull) {
    $pullResults = @()
    foreach ($image in $images) {
      try {
        docker pull $image | Out-Null
        $pullResults += [ordered]@{image=$image; result="PULLED"}
      } catch {
        $pullResults += [ordered]@{image=$image; result="OPEN"; error=$_.Exception.Message}
      }
    }
    $receipt.checks.docker_pull = $pullResults
    $receipt.actions += "PULL_SUPPORT_IMAGES"
  }
} else {
  $receipt.checks.docker_cli = "MISSING"
}

$receiptPath = Join-Path $receiptDir "LOCAL_SOL_OPEN_SUPPORT_CURRENT.json"
$receipt | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $receiptPath -Encoding UTF8
Write-Host "LOCAL_SOL_OPEN_SUPPORT COMPLETE FOR THIS PULSE"
Write-Host "Receipt: $receiptPath"
