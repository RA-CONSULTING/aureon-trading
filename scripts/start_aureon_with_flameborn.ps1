#Requires -Version 5.1
<#
.SYNOPSIS
    Unified launcher for Aureon + Flameborn (Windows PowerShell)
.DESCRIPTION
    Starts the Aureon Vault UI (port 5566), optional Flameborn Runtime (port 7331),
    and Flameborn Web App (port 4173) with shared environment.
.PARAMETER WebPort
    Port for the Flameborn web app (default 4173)
.PARAMETER RuntimePort
    Port for the Flameborn runtime (default 7331)
.PARAMETER AureonPort
    Port for the Aureon Vault UI (default 5566)
.PARAMETER StartRuntime
    Also start the Flameborn local runtime companion
.PARAMETER EnableHostTerminal
    Expose host terminal bridge through the runtime
.PARAMETER EnableSandbox
    Enable Docker sandbox terminal
#>
param(
  [int]$WebPort = 4173,
  [int]$RuntimePort = 7331,
  [int]$AureonPort = 5566,
  [switch]$StartRuntime,
  [switch]$EnableHostTerminal,
  [switch]$EnableSandbox
)

$ErrorActionPreference = "Stop"
$repo = Resolve-Path (Join-Path $PSScriptRoot "..")
$flamebornDir = Join-Path $repo "flameborn"
$logRoot = Join-Path $repo "logs"
New-Item -ItemType Directory -Force -Path $logRoot | Out-Null

function Test-Url {
  param([string]$Url)
  try {
    $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 2
    return $response.StatusCode -ge 200 -and $response.StatusCode -lt 500
  } catch {
    return $false
  }
}

function Start-NodeService {
  param(
    [string]$Name,
    [string]$WorkingDirectory,
    [string[]]$Arguments,
    [string]$HealthUrl,
    [hashtable]$ExtraEnv
  )
  if (Test-Url $HealthUrl) {
    Write-Host "  $Name already running."
    return [pscustomobject]@{ name = $Name; started = $false; reachable = $true; pid = $null; healthUrl = $HealthUrl }
  }
  foreach ($key in $ExtraEnv.Keys) {
    [Environment]::SetEnvironmentVariable($key, [string]$ExtraEnv[$key], "Process")
  }
  $stdout = Join-Path $logRoot "$Name.out.log"
  $stderr = Join-Path $logRoot "$Name.err.log"
  $proc = Start-Process -FilePath "node" -ArgumentList $Arguments -WorkingDirectory $WorkingDirectory -PassThru -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr
  $reachable = $false
  for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Milliseconds 500
    if (Test-Url $HealthUrl) { $reachable = $true; break }
  }
  $status = if ($reachable) { "ready" } else { "unreachable" }
  Write-Host "  $Name $status (PID $($proc.Id))"
  return [pscustomobject]@{ name = $Name; started = $true; reachable = $reachable; pid = $proc.Id; healthUrl = $HealthUrl; stdout = $stdout; stderr = $stderr }
}

function Start-AureonVault {
  param([int]$Port)
  $health = "http://127.0.0.1:$Port/api/status"
  if (Test-Url $health) {
    Write-Host "  Aureon Vault UI already running."
    return [pscustomobject]@{ name = "aureon-vault"; started = $false; reachable = $true; pid = $null; healthUrl = $health }
  }
  $python = "python"
  if (Test-Path "$repo\.venv\Scripts\python.exe") { $python = "$repo\.venv\Scripts\python.exe" }
  elseif (Test-Path "$repo\.venv\python.exe") { $python = "$repo\.venv\python.exe" }
  $stdout = Join-Path $logRoot "aureon-vault-ui.out.log"
  $stderr = Join-Path $logRoot "aureon-vault-ui.err.log"
  $env:AUREON_OBSIDIAN_VAULT_PATH = Join-Path $flamebornDir "logs\aureon-obsidian-vault"
  $env:AUREON_VOICE_BACKEND = "local"
  $env:AUREON_LLM_OFFLINE = "0"
  $env:AUREON_LLM_BASE_URL = "https://openrouter.ai/api/v1"
  $env:AUREON_LLM_MODEL = "qwen/qwen-2.5-7b-instruct"
  if (-not $env:AUREON_LLM_API_KEY -and $env:OPENROUTER_API_KEY) { $env:AUREON_LLM_API_KEY = $env:OPENROUTER_API_KEY }
  $proc = Start-Process -FilePath $python -ArgumentList @("scripts/runners/run_vault_ui.py","--host","127.0.0.1","--port","$Port","--no-signals","--no-ollama") -WorkingDirectory $repo -PassThru -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr
  $reachable = $false
  for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    if (Test-Url $health) { $reachable = $true; break }
  }
  $status = if ($reachable) { "ready" } else { "unreachable" }
  Write-Host "  Aureon Vault UI $status (PID $($proc.Id))"
  return [pscustomobject]@{ name = "aureon-vault"; started = $true; reachable = $reachable; pid = $proc.Id; healthUrl = $health; stdout = $stdout; stderr = $stderr }
}

Write-Host "═══════════════════════════════════════════════════════════════════════════════"
Write-Host "  AUREON + FLAMEBORN UNIFIED LAUNCHER (Windows)"
Write-Host "═══════════════════════════════════════════════════════════════════════════════"

# ── Shared environment ──
$baseEnv = @{
  HOST = "127.0.0.1"
  PORT = "$WebPort"
  FLAMEBORN_RUNTIME_HOST = "127.0.0.1"
  FLAMEBORN_RUNTIME_PORT = "$RuntimePort"
  FLAMEBORN_RUNTIME_ALLOW_REMOTE = "false"
  GARY_AUREON_ROOT = "$repo"
  AUREON_API_BASE_URL = "http://127.0.0.1:$AureonPort"
  AUREON_CHAT_PATH = "/api/message"
  AUREON_ENV_PATH = "$repo\.env"
  LOCAL_AUREON_CLI_ENABLED = "1"
  TERMINAL_ALLOW_REMOTE = "false"
  MURGE_HOST_TERMINAL_ENABLED = $(if ($EnableHostTerminal) { "1" } else { "0" })
  MURGE_SANDBOX_ENABLED = $(if ($EnableSandbox) { "1" } else { "0" })
}

# ── 1. Aureon Vault UI ──
Write-Host "[1/3] Starting Aureon Vault UI on port $AureonPort ..."
$aureon = Start-AureonVault -Port $AureonPort
if (-not $aureon.reachable) {
  Write-Error "Aureon Vault UI failed to start. Check logs: $($aureon.stderr)"
}

# ── 2. Flameborn Runtime (optional) ──
$runtime = $null
if ($StartRuntime) {
  Write-Host "[2/3] Starting Flameborn Runtime on port $RuntimePort ..."
  $runtime = Start-NodeService -Name "flameborn-runtime" -WorkingDirectory $flamebornDir -Arguments @("runtime/server.mjs") -HealthUrl "http://127.0.0.1:$RuntimePort/health" -ExtraEnv $baseEnv
} else {
  Write-Host "[2/3] Flameborn Runtime skipped (use -StartRuntime to enable)"
}

# ── 3. Flameborn Web App ──
Write-Host "[3/3] Starting Flameborn Web App on port $WebPort ..."
$web = Start-NodeService -Name "flameborn-web" -WorkingDirectory $flamebornDir -Arguments @("server.mjs") -HealthUrl "http://127.0.0.1:$WebPort/api/aureon/status" -ExtraEnv $baseEnv
if (-not $web.reachable) {
  Write-Error "Flameborn Web App failed to start. Check logs: $($web.stderr)"
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════════"
Write-Host "  AUREON + FLAMEBORN UNIFIED SYSTEM IS ONLINE"
Write-Host "═══════════════════════════════════════════════════════════════════════════════"
Write-Host "  Aureon Vault UI:  http://127.0.0.1:$AureonPort"
Write-Host "  Flameborn Web:    http://127.0.0.1:$WebPort"
if ($StartRuntime -and $runtime.reachable) {
  Write-Host "  Flameborn Runtime: http://127.0.0.1:$RuntimePort"
}
Write-Host ""
Write-Host "  Logs folder: $logRoot"
Write-Host "  Press Ctrl-C to stop all services."
Write-Host "═══════════════════════════════════════════════════════════════════════════════"

# Keep the script alive until Ctrl-C
while ($true) { Start-Sleep -Seconds 1 }
